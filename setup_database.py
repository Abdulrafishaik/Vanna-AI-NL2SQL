import sqlite3
import random
from datetime import datetime, timedelta

def create_database():
    conn = sqlite3.connect('clinic.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            date_of_birth DATE,
            gender TEXT,
            city TEXT,
            registered_date DATE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT,
            department TEXT,
            phone TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            doctor_id INTEGER,
            appointment_date DATETIME,
            status TEXT,
            notes TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS treatments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id INTEGER,
            treatment_name TEXT,
            cost REAL,
            duration_minutes INTEGER,
            FOREIGN KEY (appointment_id) REFERENCES appointments(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            invoice_date DATE,
            total_amount REAL,
            paid_amount REAL,
            status TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        )
    ''')
    
    doctors_data = [
        ("Dr. Sarah Johnson", "Cardiology", "Cardiology", "555-0101"),
        ("Dr. Michael Chen", "Cardiology", "Cardiology", "555-0102"),
        ("Dr. Emily Rodriguez", "Dermatology", "Dermatology", "555-0103"),
        ("Dr. James Wilson", "Dermatology", "Dermatology", "555-0104"),
        ("Dr. Lisa Patel", "Orthopedics", "Orthopedics", "555-0105"),
        ("Dr. Robert Taylor", "Orthopedics", "Orthopedics", "555-0106"),
        ("Dr. Maria Garcia", "Pediatrics", "Pediatrics", "555-0107"),
        ("Dr. David Kim", "Pediatrics", "Pediatrics", "555-0108"),
        ("Dr. Jennifer White", "General", "General Medicine", "555-0109"),
        ("Dr. William Brown", "General", "General Medicine", "555-0110"),
        ("Dr. Patricia Lee", "Neurology", "Neurology", "555-0111"),
        ("Dr. Thomas Martinez", "Neurology", "Neurology", "555-0112"),
        ("Dr. Barbara Anderson", "Gynecology", "Gynecology", "555-0113"),
        ("Dr. Richard Thomas", "Gynecology", "Gynecology", "555-0114"),
        ("Dr. Susan Moore", "Ophthalmology", "Ophthalmology", "555-0115"),
    ]
    
    cursor.executemany('''
        INSERT INTO doctors (name, specialization, department, phone)
        VALUES (?, ?, ?, ?)
    ''', doctors_data)
    
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", 
              "Philadelphia", "San Antonio", "San Diego", "Dallas", "Austin"]
    
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", 
                   "Michael", "Linda", "William", "Elizabeth", "David", "Barbara",
                   "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah",
                   "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
                   "Matthew", "Betty", "Anthony", "Helen", "Mark", "Sandra"]
    
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
                  "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez",
                  "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor",
                  "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
                  "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Walker"]
    
    patients = []
    for i in range(200):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        email = f"{first_name.lower()}.{last_name.lower()}@email.com"
        phone = f"555-{random.randint(100,999)}-{random.randint(1000,9999)}"
        years_ago = random.randint(18, 80)
        dob = datetime.now() - timedelta(days=years_ago*365)
        gender = random.choice(["M", "F"])
        city = random.choice(cities)
        days_ago = random.randint(1, 1095)
        registered_date = datetime.now() - timedelta(days=days_ago)
        
        patients.append((
            first_name, last_name, email, phone, 
            dob.strftime("%Y-%m-%d"), gender, city,
            registered_date.strftime("%Y-%m-%d")
        ))
    
    cursor.executemany('''
        INSERT INTO patients (first_name, last_name, email, phone, 
                             date_of_birth, gender, city, registered_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', patients)
    
    statuses = ["Scheduled", "Completed", "Cancelled", "No-Show"]
    status_weights = [0.4, 0.5, 0.05, 0.05]
    
    appointments = []
    for i in range(500):
        patient_id = random.randint(1, 200)
        doctor_id = random.randint(1, 15)
        days_ago = random.randint(1, 365)
        appointment_date = datetime.now() - timedelta(days=days_ago)
        status = random.choices(statuses, weights=status_weights)[0]
        notes = None
        if random.random() > 0.7:
            notes = f"Patient notes: {random.choice(['Routine checkup', 'Follow-up', 'Emergency', 'Consultation'])}"
        
        appointments.append((
            patient_id, doctor_id, 
            appointment_date.strftime("%Y-%m-%d %H:%M:%S"),
            status, notes
        ))
    
    cursor.executemany('''
        INSERT INTO appointments (patient_id, doctor_id, appointment_date, status, notes)
        VALUES (?, ?, ?, ?, ?)
    ''', appointments)
    
    treatment_names = ["X-Ray", "Blood Test", "MRI Scan", "CT Scan", "Ultrasound",
                       "Physical Therapy", "Consultation", "Vaccination", "Surgery",
                       "Dental Cleaning", "Eye Exam", "ECG", "Biopsy", "Chemotherapy"]
    
    treatments = []
    cursor.execute("SELECT id FROM appointments WHERE status = 'Completed'")
    completed_appointments = [row[0] for row in cursor.fetchall()]
    
    for appt_id in random.sample(completed_appointments, min(350, len(completed_appointments))):
        treatment_name = random.choice(treatment_names)
        cost = round(random.uniform(50, 5000), 2)
        duration = random.randint(15, 180)
        treatments.append((appt_id, treatment_name, cost, duration))
    
    cursor.executemany('''
        INSERT INTO treatments (appointment_id, treatment_name, cost, duration_minutes)
        VALUES (?, ?, ?, ?)
    ''', treatments)
    
    invoice_statuses = ["Paid", "Pending", "Overdue"]
    invoice_weights = [0.6, 0.25, 0.15]
    
    invoices = []
    for patient_id in range(1, 201):
        num_invoices = random.choices([1, 2, 3, 4], weights=[0.5, 0.3, 0.15, 0.05])[0]
        
        for _ in range(num_invoices):
            invoice_date = datetime.now() - timedelta(days=random.randint(1, 365))
            total_amount = round(random.uniform(100, 5000), 2)
            status = random.choices(invoice_statuses, weights=invoice_weights)[0]
            
            if status == "Paid":
                paid_amount = total_amount
            elif status == "Pending":
                paid_amount = 0
            else:
                paid_amount = round(total_amount * random.uniform(0, 0.5), 2)
            
            invoices.append((
                patient_id,
                invoice_date.strftime("%Y-%m-%d"),
                total_amount,
                paid_amount,
                status
            ))
    
    cursor.executemany('''
        INSERT INTO invoices (patient_id, invoice_date, total_amount, paid_amount, status)
        VALUES (?, ?, ?, ?, ?)
    ''', invoices)
    
    conn.commit()
    conn.close()
    
    print(f"Created {len(patients)} patients, {len(doctors_data)} doctors, {len(appointments)} appointments, {len(treatments)} treatments, {len(invoices)} invoices")

if __name__ == "__main__":
    create_database()