from typing import Optional
from fastapi import APIRouter, HTTPException
from app.services.dental_service import dental_service
from app.schemas.appointment import AppointmentCreate, StatusUpdate

router = APIRouter(prefix="/api/clinics/{clinic_id}", tags=["Appointments & Slots"])

@router.get("/appointments")
def list_appointments(clinic_id: str):
    """Fetch all appointments for a specific clinic."""
    return dental_service.get_appointments(clinic_id)

@router.post("/appointments")
def create_appointment(clinic_id: str, data: AppointmentCreate):
    """Book a new appointment in the clinic database."""
    res = dental_service.book_appointment(
        clinic_id=clinic_id,
        patient_name=data.patient_name,
        patient_phone=data.patient_phone,
        appointment_date=data.appointment_date,
        appointment_time=data.appointment_time,
        treatment_type=data.treatment_type,
        doctor_id=data.doctor_id,
        notes=data.notes,
        booking_source=data.booking_source or "Manual Dashboard"
    )
    return res

@router.patch("/appointments/{app_id}")
def update_appointment_status(clinic_id: str, app_id: str, payload: StatusUpdate):
    """Update status of appointment (e.g., Arrived, Completed, Cancelled)."""
    ok = dental_service.update_appointment_status(app_id, payload.status)
    if not ok:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"success": True, "app_id": app_id, "new_status": payload.status}

@router.get("/slots")
def get_open_slots(clinic_id: str, date: str = "today", time_pref: str = "any", doctor_id: Optional[str] = None):
    """Real-time calculation of available slots after subtracting booked appointments."""
    slots = dental_service.get_available_slots(clinic_id, date, time_pref, doctor_id)
    return {"clinic_id": clinic_id, "date": date, "available_slots": slots}
