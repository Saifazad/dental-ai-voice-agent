import sqlite3
from app.db.connection import get_connection

def init_db():
    """Initialize database tables with multi-tenant structure and seed demo data."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Clinics table (Tenants)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clinics (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        city TEXT NOT NULL,
        address TEXT NOT NULL,
        phone_number TEXT NOT NULL,
        emergency_phone TEXT NOT NULL,
        assistant_name TEXT NOT NULL DEFAULT 'Aanya',
        assistant_tone TEXT NOT NULL DEFAULT 'Warm, Reassuring & Polite (Hinglish/English)',
        opening_time TEXT NOT NULL DEFAULT '10:00 AM',
        closing_time TEXT NOT NULL DEFAULT '08:30 PM',
        lunch_start TEXT NOT NULL DEFAULT '01:30 PM',
        lunch_end TEXT NOT NULL DEFAULT '02:30 PM',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. Doctors table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctors (
        id TEXT PRIMARY KEY,
        clinic_id TEXT NOT NULL,
        name TEXT NOT NULL,
        qualification TEXT NOT NULL,
        specialization TEXT NOT NULL,
        experience_years INTEGER NOT NULL DEFAULT 10,
        consultation_fee INTEGER NOT NULL DEFAULT 500,
        is_available INTEGER NOT NULL DEFAULT 1,
        working_days TEXT NOT NULL DEFAULT 'Mon,Tue,Wed,Thu,Fri,Sat',
        FOREIGN KEY (clinic_id) REFERENCES clinics(id)
    )
    """)

    # 3. Services & Pricing table (Dynamic per clinic)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS services (
        id TEXT PRIMARY KEY,
        clinic_id TEXT NOT NULL,
        category TEXT NOT NULL,
        name TEXT NOT NULL,
        price_range TEXT NOT NULL,
        min_price INTEGER NOT NULL,
        duration_mins INTEGER NOT NULL DEFAULT 30,
        description TEXT,
        FOREIGN KEY (clinic_id) REFERENCES clinics(id)
    )
    """)

    # 4. Appointments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id TEXT PRIMARY KEY,
        clinic_id TEXT NOT NULL,
        doctor_id TEXT,
        doctor_name TEXT,
        patient_name TEXT NOT NULL,
        patient_phone TEXT NOT NULL,
        appointment_date TEXT NOT NULL,
        appointment_time TEXT NOT NULL,
        treatment_type TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Confirmed (AI Voice)',
        is_emergency INTEGER NOT NULL DEFAULT 0,
        notes TEXT,
        booking_source TEXT NOT NULL DEFAULT 'AI Voice Agent',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (clinic_id) REFERENCES clinics(id)
    )
    """)

    # 5. Call Logs table (Recordings, Transcripts, Summaries)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS call_logs (
        id TEXT PRIMARY KEY,
        clinic_id TEXT NOT NULL,
        caller_name TEXT NOT NULL,
        caller_phone TEXT NOT NULL,
        duration_seconds INTEGER NOT NULL,
        timestamp TEXT NOT NULL,
        summary TEXT NOT NULL,
        transcript TEXT NOT NULL,
        sentiment TEXT NOT NULL DEFAULT 'Satisfied',
        is_emergency INTEGER NOT NULL DEFAULT 0,
        action_taken TEXT NOT NULL,
        FOREIGN KEY (clinic_id) REFERENCES clinics(id)
    )
    """)

    # 6. Clinic Integrations table (CRM, Google Sheets, Google Calendar, WhatsApp)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clinic_integrations (
        clinic_id TEXT PRIMARY KEY,
        google_sheets_enabled INTEGER DEFAULT 1,
        google_sheet_url TEXT DEFAULT 'https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit',
        google_sheet_id TEXT DEFAULT '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms',
        google_calendar_enabled INTEGER DEFAULT 1,
        google_calendar_email TEXT DEFAULT 'dr.rohan.dental@gmail.com',
        crm_type TEXT DEFAULT 'Dental Clinic CRM (Desktop)',
        crm_webhook_url TEXT DEFAULT 'http://localhost:3000/api/v1/appointments',
        crm_base_url TEXT DEFAULT 'http://localhost:3000',
        crm_enabled INTEGER DEFAULT 1,
        whatsapp_enabled INTEGER DEFAULT 1,
        last_synced_at TEXT DEFAULT 'Just Now',
        FOREIGN KEY (clinic_id) REFERENCES clinics(id)
    )
    """)

    # Safe migration for new CRM columns
    for col_name, col_type in [
        ("crm_appointment_id", "TEXT"),
        ("crm_sync_status", "TEXT DEFAULT 'LOCAL_ONLY'"),
        ("crm_synced_at", "TEXT")
    ]:
        try:
            cursor.execute(f"ALTER TABLE appointments ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass

    for col_name, col_type in [
        ("crm_base_url", "TEXT DEFAULT 'http://localhost:3000'"),
        ("crm_status", "TEXT DEFAULT 'Connected'"),
        ("crm_api_key", "TEXT DEFAULT ''")
    ]:
        try:
            cursor.execute(f"ALTER TABLE clinic_integrations ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()
