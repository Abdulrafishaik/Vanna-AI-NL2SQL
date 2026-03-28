from vanna_setup import setup_vanna_agent

EXAMPLES = [
    ("How many patients do we have?",
     "SELECT COUNT(*) AS total_patients FROM patients"),
    ("List all doctors and their specializations",
     "SELECT name, specialization FROM doctors"),
    ("Show me appointments for last month",
     "SELECT * FROM appointments WHERE appointment_date >= date('now', '-1 month')"),
    ("Which doctor has the most appointments?",
     "SELECT d.name, COUNT(a.id) AS appointment_count FROM doctors d JOIN appointments a ON d.id = a.doctor_id GROUP BY d.id ORDER BY appointment_count DESC LIMIT 1"),
    ("What is the total revenue?",
     "SELECT SUM(total_amount) AS total_revenue FROM invoices WHERE status = 'Paid'"),
    ("Show revenue by doctor",
     "SELECT d.name, SUM(i.total_amount) AS total_revenue FROM invoices i JOIN appointments a ON a.patient_id = i.patient_id JOIN doctors d ON d.id = a.doctor_id GROUP BY d.name ORDER BY total_revenue DESC"),
    ("How many cancelled appointments last quarter?",
     "SELECT COUNT(*) AS cancelled_count FROM appointments WHERE status = 'Cancelled' AND appointment_date >= date('now', '-3 months')"),
    ("Top 5 patients by spending",
     "SELECT p.first_name, p.last_name, SUM(i.total_amount) AS total_spent FROM patients p JOIN invoices i ON p.id = i.patient_id GROUP BY p.id ORDER BY total_spent DESC LIMIT 5"),
    ("Average treatment cost by specialization",
     "SELECT d.specialization, AVG(t.cost) AS avg_cost FROM treatments t JOIN appointments a ON t.appointment_id = a.id JOIN doctors d ON a.doctor_id = d.id GROUP BY d.specialization"),
    ("Show monthly appointment count for the past 6 months",
     "SELECT strftime('%Y-%m', appointment_date) AS month, COUNT(*) AS appointment_count FROM appointments WHERE appointment_date >= date('now', '-6 months') GROUP BY month ORDER BY month"),
    ("Which city has the most patients?",
     "SELECT city, COUNT(*) AS patient_count FROM patients GROUP BY city ORDER BY patient_count DESC LIMIT 1"),
    ("List patients who visited more than 3 times",
     "SELECT p.first_name, p.last_name, COUNT(a.id) AS visit_count FROM patients p JOIN appointments a ON p.id = a.patient_id GROUP BY p.id HAVING COUNT(a.id) > 3"),
    ("Show unpaid invoices",
     "SELECT * FROM invoices WHERE status = 'Pending' OR status = 'Overdue'"),
    ("What percentage of appointments are no-shows?",
     "SELECT ROUND(100.0 * SUM(CASE WHEN status = 'No-Show' THEN 1 ELSE 0 END) / COUNT(*), 2) AS no_show_pct FROM appointments"),
    ("Show the busiest day of the week for appointments",
     "SELECT strftime('%w', appointment_date) AS day_of_week, COUNT(*) AS cnt FROM appointments GROUP BY day_of_week ORDER BY cnt DESC LIMIT 1"),
    ("Revenue trend by month",
     "SELECT strftime('%Y-%m', invoice_date) AS month, SUM(total_amount) AS revenue FROM invoices WHERE status = 'Paid' GROUP BY month ORDER BY month"),
]

def seed_memory():
    agent = setup_vanna_agent()
    count = 0
    for question, sql in EXAMPLES:
        try:
            agent.agent_memory.add_example(question=question, sql=sql)
            count += 1
            print(f"✓ {question}")
        except Exception as e:
            print(f"✗ {question} — {e}")
    print(f"\n{'='*50}")
    print(f"Seeded {count}/{len(EXAMPLES)} examples")
    print(f"{'='*50}")

if __name__ == "__main__":
    seed_memory()