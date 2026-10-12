"""
Backward compatibility layer for dental_logic module.
Re-exports from app.services.triage_service and app.services.slot_service.
"""
from app.services.triage_service import evaluate_emergency, EMERGENCY_KEYWORDS
from app.services.slot_service import get_slots_for_date

DENTAL_SERVICES = {
    "cleaning": {"name": "Teeth Cleaning & Polishing (Scaling)", "price_range": "₹1,000 - ₹1,500", "duration_mins": 30},
    "root_canal": {"name": "Root Canal Treatment (RCT)", "price_range": "₹3,500 - ₹6,000", "duration_mins": 45},
    "extraction": {"name": "Tooth Extraction", "price_range": "₹800 - ₹2,000", "duration_mins": 30},
    "filling": {"name": "Cavity Filling (Composite)", "price_range": "₹1,200 - ₹2,500", "duration_mins": 30},
    "braces": {"name": "Orthodontic Braces / Aligners", "price_range": "₹25,000 - ₹60,000", "duration_mins": 45},
    "consultation": {"name": "General Dental Consultation", "price_range": "₹300 - ₹500", "duration_mins": 20},
}

__all__ = ["evaluate_emergency", "EMERGENCY_KEYWORDS", "get_slots_for_date", "DENTAL_SERVICES"]
