from pydantic import BaseModel
from typing import Optional

class AppointmentCreate(BaseModel):
    patient_name: str
    patient_phone: str
    appointment_date: str
    appointment_time: str
    treatment_type: str = "General Consultation"
    doctor_id: Optional[str] = None
    notes: Optional[str] = ""
    booking_source: Optional[str] = "Manual Dashboard"

class StatusUpdate(BaseModel):
    status: str
