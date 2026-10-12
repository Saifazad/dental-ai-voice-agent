from datetime import datetime, date, timedelta
from typing import List, Optional
from app.db.connection import get_connection
from app.integrations.crm_client import crm_client

def normalize_date(date_str: str) -> str:
    """Normalize colloquial Hindi/English date strings into standard YYYY-MM-DD format."""
    if not date_str:
        return date.today().strftime("%Y-%m-%d")
    s = str(date_str).strip().lower()
    today = date.today()
    if s in ("today", "aaj"):
        return today.strftime("%Y-%m-%d")
    elif s in ("tomorrow", "kal"):
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")
    elif s in ("day after tomorrow", "parso"):
        return (today + timedelta(days=2)).strftime("%Y-%m-%d")
    elif s in ("yesterday", "beeta kal"):
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")
    return date_str

def get_slots_for_date(date_str: str, time_preference: str = "any") -> List[str]:
    """Generate default slot recommendations for a date and preference."""
    all_morning_slots = ["10:30 AM", "11:15 AM", "12:00 PM"]
    all_evening_slots = ["05:00 PM", "05:45 PM", "06:30 PM", "07:15 PM"]
    pref = (time_preference or "any").lower()
    if "morning" in pref or "subah" in pref:
        return all_morning_slots
    elif "evening" in pref or "shaam" in pref or "afternoon" in pref:
        return all_evening_slots
    return ["11:15 AM", "05:00 PM", "06:30 PM"]

def get_available_slots(clinic_id: str, date_str: str, time_preference: str = "any", doctor_id: Optional[str] = None) -> List[str]:
    """
    Dynamically calculate open slots by checking Dental CRM first,
    falling back to SQLite database schedule subtraction.
    """
    target_date = normalize_date(date_str)

    # 1. Attempt live check from Dental Clinic CRM (PostgreSQL)
    crm_slots = crm_client.get_availability(target_date, time_preference, doctor_id)
    if crm_slots:
        return crm_slots

    # 2. Fallback to local SQLite calculation
    conn = get_connection()
    cursor = conn.cursor()

    morning_slots = ["10:30 AM", "11:15 AM", "12:00 PM", "12:45 PM"]
    evening_slots = ["03:30 PM", "04:15 PM", "05:00 PM", "05:45 PM", "06:30 PM", "07:15 PM"]

    pref = (time_preference or "any").lower()
    if "morning" in pref or "subah" in pref:
        candidate_slots = morning_slots
    elif "evening" in pref or "shaam" in pref or "afternoon" in pref or "dopahar" in pref:
        candidate_slots = evening_slots
    else:
        candidate_slots = ["11:15 AM", "12:00 PM", "04:15 PM", "05:00 PM", "06:30 PM"]

    # Fetch already booked times for this clinic & date
    cursor.execute("""
    SELECT appointment_time FROM appointments 
    WHERE clinic_id = ? AND appointment_date = ? AND status != 'Cancelled'
    """, (clinic_id, target_date))
    booked_times = {row["appointment_time"].strip().upper() for row in cursor.fetchall()}
    conn.close()

    # Filter out booked slots
    open_slots = [s for s in candidate_slots if s.strip().upper() not in booked_times]
    return open_slots if open_slots else ["04:15 PM (Emergency Hold)", "05:30 PM"]
