from typing import Dict, Any

EMERGENCY_KEYWORDS = [
    "severe pain", "unbearable", "bleeding", "khoon", "dard", "bahut dard",
    "swelling", "soojan", "broken tooth", "accident", "trauma", "pus", "infection",
    "urgent", "emergency"
]

def evaluate_emergency(symptoms: str) -> Dict[str, Any]:
    """Check if patient's symptoms require immediate emergency attention."""
    symptoms_lower = (symptoms or "").lower()
    is_emergency = any(kw in symptoms_lower for kw in EMERGENCY_KEYWORDS)

    if is_emergency:
        return {
            "is_emergency": True,
            "message": "Yeh emergency situation lag rahi hai. Patient ko turant clinic aane ko bolein ya on-call doctor se baat karwayein.",
            "action": "transfer_call_or_urgent_visit"
        }
    return {
        "is_emergency": False,
        "message": "Normal consultation slot book kiya ja sakta hai.",
        "action": "proceed_with_booking"
    }
