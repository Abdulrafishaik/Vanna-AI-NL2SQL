import os
import re
import sqlite3
import time
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Any
from dotenv import load_dotenv

load_dotenv()

# ── Gemini setup ───────────────────────────────────────────────────────────────
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
# gemini-1.5-flash has a separate free quota from gemini-2.0-flash
gemini = genai.GenerativeModel("gemini-2.0-flash")

DB_PATH = "clinic.db"

SYSTEM_PROMPT = """You are a helpful assistant for a medical clinic management system.

You have two modes:

MODE 1 — CASUAL CONVERSATION
For greetings or off-topic questions (e.g. "hello", "how are you", "what can you do"),
respond warmly and briefly. Mention you are designed to help with clinic data queries.
Do NOT generate SQL for these.

MODE 2 — DATABASE QUERIES
For any question about patients, doctors, appointments, treatments, invoices or clinic
data, output ONLY a raw SQLite SELECT query — no explanation, no markdown, no backticks.

DATABASE SCHEMA:
  patients     (id, first_name, last_name, email, phone, date_of_birth, gender, city, registered_date)
  doctors      (id, name, specialization, department, phone)
  appointments (id, patient_id, doctor_id, appointment_date, status, notes)
               status values: 'Scheduled' | 'Completed' | 'Cancelled' | 'No-Show'
  treatments   (id, appointment_id, treatment_name, cost, duration_minutes)
  invoices     (id, patient_id, invoice_date, total_amount, paid_amount, status)
               status values: 'Paid' | 'Pending' | 'Overdue'

EXAMPLE Q&A (reference these for generating SQL):
Q: How many patients do we have?
A: SELECT COUNT(*) AS total_patients FROM patients

Q: List all doctors and their specializations
A: SELECT name, specialization FROM doctors

Q: Which doctor has the most appointments?
A: SELECT d.name, COUNT(a.id) AS cnt FROM doctors d JOIN appointments a ON d.id=a.doctor_id GROUP BY d.id ORDER BY cnt DESC LIMIT 1

Q: Total revenue
A: SELECT SUM(total_amount) AS total_revenue FROM invoices WHERE status='Paid'

Q: Top 5 patients by spending
A: SELECT p.first_name, p.last_name, SUM(i.total_amount) AS total FROM patients p JOIN invoices i ON p.id=i.patient_id GROUP BY p.id ORDER BY total DESC LIMIT 5

Q: Show unpaid invoices count
A: SELECT COUNT(*) AS unpaid FROM invoices WHERE status IN ('Pending','Overdue')

Q: What percentage of appointments are no-shows?
A: SELECT ROUND(100.0*SUM(CASE WHEN status='No-Show' THEN 1 ELSE 0 END)/COUNT(*),2) AS pct FROM appointments

Q: Which city has the most patients?
A: SELECT city, COUNT(*) AS cnt FROM patients GROUP BY city ORDER BY cnt DESC LIMIT 1

Q: Average treatment cost by specialization
A: SELECT d.specialization, AVG(t.cost) AS avg_cost FROM treatments t JOIN appointments a ON t.appointment_id=a.id JOIN doctors d ON a.doctor_id=d.id GROUP BY d.specialization

Q: Revenue trend by month
A: SELECT strftime('%Y-%m', invoice_date) AS month, SUM(total_amount) AS revenue FROM invoices WHERE status='Paid' GROUP BY month ORDER BY month

RULES:
- Only SELECT queries. Never INSERT/UPDATE/DELETE/DROP/CREATE.
- Output ONLY raw SQL for database questions — nothing else at all.
- Use SQLite syntax (use strftime for date operations).
- For non-clinic questions reply conversationally only, never output SQL."""

SUMMARY_PROMPT = """The user asked: "{question}"
SQL executed: {sql}
Columns: {columns}
Results (first 20 rows): {rows}

Write a clear, friendly 1-3 sentence summary of what the data shows. No SQL. Plain English only."""


# ── FastAPI app ────────────────────────────────────────────────────────────────
app = FastAPI(title="Clinic NL2SQL Chatbot", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    message: str
    sql_query: Optional[str] = None
    columns: Optional[List[str]] = None
    rows: Optional[List[Any]] = None
    row_count: int = 0


# ── Helpers ────────────────────────────────────────────────────────────────────
def is_sql(text: str) -> bool:
    return bool(re.match(r"^\s*SELECT\s", text, re.IGNORECASE))

def clean_sql(text: str) -> str:
    text = re.sub(r"```sql", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```", "", text)
    return text.strip()

def validate_sql(sql: str) -> bool:
    upper = sql.upper()
    blocked = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE",
               "ALTER", "TRUNCATE", "EXEC", "MERGE", "GRANT", "REVOKE"]
    return (
        not any(re.search(rf"\b{k}\b", upper) for k in blocked)
        and upper.strip().startswith("SELECT")
    )

def run_sql(sql: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    conn.close()
    return cols, rows

def call_gemini(prompt: str, retries: int = 3) -> str:
    """Call Gemini with automatic retry on 429 rate limit."""
    for attempt in range(retries):
        try:
            resp = gemini.generate_content(f"{SYSTEM_PROMPT}\n\nUser: {prompt}")
            return resp.text.strip()
        except Exception as e:
            err = str(e)
            if "429" in err and attempt < retries - 1:
                wait = 35 * (attempt + 1)   # wait 35s, 70s, ...
                print(f"[rate limit] waiting {wait}s before retry {attempt+2}/{retries}")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Gemini call failed after retries")

def summarise(question: str, sql: str, cols: list, rows: list) -> str:
    prompt = SUMMARY_PROMPT.format(
        question=question, sql=sql, columns=cols, rows=rows[:20]
    )
    resp = gemini.generate_content(prompt)
    return resp.text.strip()


# ── Endpoints ──────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "model": "gemini-1.5-flash", "database": "clinic.db"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: QuestionRequest):
    q = (request.question or "").strip()
    if not q:
        raise HTTPException(400, "Question cannot be empty")
    if len(q) > 500:
        raise HTTPException(400, "Question too long (max 500 chars)")

    # Step 1: Ask Gemini — returns raw SQL or a conversational reply
    try:
        reply = call_gemini(q)
    except Exception as e:
        raise HTTPException(500, f"Gemini error: {e}")

    # Step 2: Conversational reply — return directly
    if not is_sql(reply):
        return ChatResponse(message=reply, row_count=0)

    # Step 3: Clean + validate SQL
    sql = clean_sql(reply)
    if not validate_sql(sql):
        return ChatResponse(
            message="I can only run SELECT queries for safety.",
            row_count=0
        )

    # Step 4: Execute SQL against clinic.db
    try:
        cols, rows = run_sql(sql)
    except sqlite3.Error as e:
        # Auto-fix attempt
        try:
            fix_resp = gemini.generate_content(
                f"Fix this SQLite query.\nError: {e}\nQuery: {sql}\nReturn ONLY the corrected SQL, nothing else."
            )
            sql = clean_sql(fix_resp.text.strip())
            cols, rows = run_sql(sql)
        except Exception as e2:
            raise HTTPException(400, f"Database error: {e2}")

    # Step 5: Ask Gemini to summarise results in natural language
    try:
        summary = summarise(q, sql, cols, rows)
    except Exception:
        summary = f"Found {len(rows)} result(s)."

    return ChatResponse(
        message=summary,
        sql_query=sql,
        columns=cols,
        rows=[list(r) for r in rows],
        row_count=len(rows)
    )