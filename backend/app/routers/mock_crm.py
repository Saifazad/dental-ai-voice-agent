import uuid
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Query, Body, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/mock-crm/api/v1", tags=["Built-in Sample CRM (For Testing)"])

# In-memory Mock CRM State (Simulates an external Clinic CRM)
MOCK_CLINIC = {
    "id": "crm_clinic_apex",
    "name": "Apex Dental & Implant Center (Live CRM)",
    "city": "South Delhi",
    "address": "M-Block Market, Greater Kailash 2, New Delhi",
    "phone": "+91 11 4982 7700",
    "opening_time": "10:00 AM",
    "closing_time": "08:30 PM",
    "lunch_start": "01:30 PM",
    "lunch_end": "02:30 PM"
}

MOCK_DOCTORS = [
    {
        "id": "doc_rohit",
        "clinic_id": "crm_clinic_apex",
        "name": "Dr. Rohit Sharma",
        "qualification": "BDS, MDS (Oral & Maxillofacial)",
        "specialization": "Implantologist & Cosmetic Surgeon",
        "experience_years": 12,
        "consultation_fee": 800,
        "is_available": 1,
        "working_days": "Mon,Tue,Wed,Thu,Fri,Sat"
    },
    {
        "id": "doc_sneha",
        "clinic_id": "crm_clinic_apex",
        "name": "Dr. Sneha Kapoor",
        "qualification": "BDS, MDS (Orthodontics)",
        "specialization": "Invisalign & Braces Specialist",
        "experience_years": 8,
        "consultation_fee": 600,
        "is_available": 1,
        "working_days": "Mon,Wed,Fri,Sat"
    },
    {
        "id": "doc_ananya",
        "clinic_id": "crm_clinic_apex",
        "name": "Dr. Ananya Sen",
        "qualification": "BDS, Fellowship in Endodontics",
        "specialization": "Root Canal Specialist",
        "experience_years": 6,
        "consultation_fee": 500,
        "is_available": 1,
        "working_days": "Tue,Thu,Sat"
    }
]

MOCK_SERVICES = [
    {
        "id": "srv_rct",
        "clinic_id": "crm_clinic_apex",
        "category": "Endodontics",
        "name": "Root Canal Treatment (Single Sitting)",
        "price_range": "₹4,500 - ₹8,000",
        "min_price": 4500,
        "duration_mins": 45,
        "description": "Painless digital single-sitting rotary RCT with laser sterilization"
    },
    {
        "id": "srv_implant",
        "clinic_id": "crm_clinic_apex",
        "category": "Implantology",
        "name": "Osstem Dental Implant with Crown",
        "price_range": "₹25,000 - ₹38,000",
        "min_price": 25000,
        "duration_mins": 60,
        "description": "Grade 4 Titanium implant with lifetime manufacturer warranty"
    },
    {
        "id": "srv_whitening",
        "clinic_id": "crm_clinic_apex",
        "category": "Cosmetic",
        "name": "Laser Teeth Whitening (Zoom)",
        "price_range": "₹7,000 - ₹12,000",
        "min_price": 7000,
        "duration_mins": 45,
        "description": "Up to 8 shades whiter in a single 45-minute clinical laser session"
    },
    {
        "id": "srv_cleaning",
        "clinic_id": "crm_clinic_apex",
        "category": "Preventive",
        "name": "Ultrasonic Scaling & Deep Polishing",
        "price_range": "₹1,500 - ₹2,500",
        "min_price": 1500,
        "duration_mins": 30,
        "description": "Full mouth ultrasonic tartar removal with anti-stain polishing"
    }
]

today_str = date.today().strftime("%Y-%m-%d")
MOCK_APPOINTMENTS: List[Dict[str, Any]] = [
    {
        "id": "crm_app_101",
        "clinic_id": "crm_clinic_apex",
        "doctor_id": "doc_rohit",
        "doctor_name": "Dr. Rohit Sharma",
        "patient_name": "Vikram Malhotra",
        "patient_phone": "+91 98112 34567",
        "appointment_date": today_str,
        "appointment_time": "11:00 AM",
        "treatment_type": "Root Canal Treatment",
        "status": "Confirmed",
        "is_emergency": 0,
        "booking_source": "Dental CRM (Front Desk)",
        "notes": "Patient reports mild sensitivity in lower molar",
        "created_at": datetime.now().isoformat()
    },
    {
        "id": "crm_app_102",
        "clinic_id": "crm_clinic_apex",
        "doctor_id": "doc_sneha",
        "doctor_name": "Dr. Sneha Kapoor",
        "patient_name": "Pooja Singhania",
        "patient_phone": "+91 99201 88321",
        "appointment_date": today_str,
        "appointment_time": "03:00 PM",
        "treatment_type": "Invisalign Consultation",
        "status": "Confirmed",
        "is_emergency": 0,
        "booking_source": "Dental CRM (Portal)",
        "notes": "Routine aligner progress checkup",
        "created_at": datetime.now().isoformat()
    }
]

# Pydantic Schemas for Mock CRM
class MockAppointmentCreate(BaseModel):
    patient_name: str
    patient_phone: str
    appointment_date: str
    appointment_time: str
    treatment_type: Optional[str] = "General Consultation"
    treatment_name: Optional[str] = None
    doctor_id: Optional[str] = None
    doctor_name: Optional[str] = None
    notes: Optional[str] = ""
    booked_by: Optional[str] = "AI Voice Receptionist"
    is_emergency: Optional[int] = 0

@router.get("/clinic")
def get_clinic():
    return {"success": True, "clinic": MOCK_CLINIC}

@router.get("/doctors")
def get_doctors():
    return {"success": True, "doctors": MOCK_DOCTORS}

@router.patch("/doctors")
def update_doctor(payload: Dict[str, Any] = Body(...)):
    doc_id = payload.get("id")
    for doc in MOCK_DOCTORS:
        if doc["id"] == doc_id:
            if "is_available" in payload:
                doc["is_available"] = int(payload["is_available"])
            return {"success": True, "doctor": doc}
    raise HTTPException(status_code=404, detail="Doctor not found in CRM")

@router.get("/services")
def get_services():
    return {"success": True, "services": MOCK_SERVICES}

@router.put("/services")
def update_service(payload: Dict[str, Any] = Body(...)):
    srv_id = payload.get("id")
    for srv in MOCK_SERVICES:
        if srv["id"] == srv_id:
            if "price_range" in payload:
                srv["price_range"] = payload["price_range"]
            if "base_price" in payload:
                srv["min_price"] = int(payload["base_price"])
            return {"success": True, "service": srv}
    raise HTTPException(status_code=404, detail="Service not found in CRM")

@router.get("/appointments")
def get_appointments():
    return {"success": True, "appointments": MOCK_APPOINTMENTS}

@router.post("/appointments")
def create_appointment(data: MockAppointmentCreate):
    new_id = f"crm_app_{uuid.uuid4().hex[:6]}"
    doc_name = data.doctor_name
    if not doc_name and data.doctor_id:
        doc = next((d for d in MOCK_DOCTORS if d["id"] == data.doctor_id), None)
        doc_name = doc["name"] if doc else "Dr. Rohit Sharma"
    elif not doc_name:
        doc_name = "Dr. Rohit Sharma"

    app_obj = {
        "id": new_id,
        "clinic_id": MOCK_CLINIC["id"],
        "doctor_id": data.doctor_id or "doc_rohit",
        "doctor_name": doc_name,
        "patient_name": data.patient_name,
        "patient_phone": data.patient_phone,
        "appointment_date": data.appointment_date,
        "appointment_time": data.appointment_time,
        "treatment_type": data.treatment_name or data.treatment_type,
        "status": "Confirmed (Live CRM)",
        "is_emergency": data.is_emergency or 0,
        "booking_source": data.booked_by or "AI Voice Receptionist",
        "notes": data.notes or "Booked via AI Voice Call",
        "created_at": datetime.now().isoformat()
    }
    MOCK_APPOINTMENTS.insert(0, app_obj)
    return {
        "success": True,
        "appointment": app_obj,
        "id": new_id,
        "message": f"Successfully created appointment {new_id} in Dental CRM"
    }

@router.patch("/appointments")
def update_appointment_status(payload: Dict[str, Any] = Body(...)):
    app_id = payload.get("id")
    new_status = payload.get("status")
    for app in MOCK_APPOINTMENTS:
        if app["id"] == app_id:
            app["status"] = new_status
            return {"success": True, "appointment": app}
    raise HTTPException(status_code=404, detail="Appointment not found in CRM")

@router.get("/availability")
def get_availability(date: str = Query("today"), time_preference: str = Query("any"), doctor_id: Optional[str] = None):
    # Return realistic time slots
    all_slots = ["10:30 AM", "11:30 AM", "12:30 PM", "03:00 PM", "04:30 PM", "05:30 PM", "06:30 PM"]
    # Filter out already booked slots
    booked_times = [a["appointment_time"] for a in MOCK_APPOINTMENTS if a["appointment_date"] == date]
    available = [s for s in all_slots if s not in booked_times]
    return {
        "success": True,
        "date": date,
        "available_slots": available
    }
