from pydantic import BaseModel
from typing import Optional

class VoiceSimulationRequest(BaseModel):
    clinic_id: str
    scenario: str  # e.g. "book_rct", "pricing_scaling", "emergency_bleeding", "check_slots"
    patient_name: Optional[str] = "Rahul Verma"
    patient_phone: Optional[str] = "+91 98450 77123"
    custom_message: Optional[str] = None
