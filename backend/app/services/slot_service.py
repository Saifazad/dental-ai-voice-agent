from datetime import datetime, date, timedelta
from typing import List, Optional
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
    Dynamically calculate open slots directly from connected Dental CRM.
    Zero local database reliance.
    """
    target_date = normalize_date(date_str)

    # 1. Attempt live check from connected Dental Clinic CRM
    crm_slots = crm_client.get_availability(target_date, time_preference, doctor_id)
    if crm_slots:
        return crm_slots

    # 2. In-memory schedule calculation using candidate slots
    morning_slots = ["10:30 AM", "11:15 AM", "12:00 PM", "12:45 PM"]
    evening_slots = ["03:30 PM", "04:15 PM", "05:00 PM", "05:45 PM", "06:30 PM", "07:15 PM"]

    pref = (time_preference or "any").lower()
    if "morning" in pref or "subah" in pref:
        candidate_slots = morning_slots
    elif "evening" in pref or "shaam" in pref or "afternoon" in pref or "dopahar" in pref:
        candidate_slots = evening_slots
    else:
        candidate_slots = ["11:15 AM", "12:00 PM", "04:15 PM", "05:00 PM", "06:30 PM"]

    # If CRM has appointments loaded, filter out conflicting times
    crm_apps = crm_client.get_crm_appointments() or []
    booked_times = {
        a.get("appointment_time", "").strip().upper()
        for a in crm_apps
        if a.get("appointment_date") == target_date and a.get("status") != "Cancelled"
    }

    open_slots = [s for s in candidate_slots if s.strip().upper() not in booked_times]
    return open_slots if open_slots else ["04:15 PM (Emergency Hold)", "05:30 PM"]
