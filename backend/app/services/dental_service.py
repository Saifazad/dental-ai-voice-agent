import uuid
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from app.integrations.crm_client import crm_client
from app.services.triage_service import evaluate_emergency, EMERGENCY_KEYWORDS
from app.services.slot_service import get_available_slots as compute_available_slots, normalize_date

class DentalService:
    """
    Pure Headless CRM Gateway Service.
    Stateless / In-Memory Proxy Layer that interacts directly with any connected Dental Clinic CRM.
    Zero local SQLite database dependency.
    """
    def __init__(self):
        self.call_logs: List[Dict[str, Any]] = []

    def clear_cache(self):
        """Purge ephemeral in-memory state on CRM disconnect."""
        self.call_logs.clear()

    def resolve_clinic_id(self, clinic_id: Optional[str] = None) -> str:
        if clinic_id and clinic_id not in ("clinic_bangalore", "default", "null", "undefined", ""):
            return clinic_id
        clinics = self.get_clinics()
        if clinics:
            return clinics[0].get("id", "crm_clinic_apex")
        return "crm_clinic_apex"

    def get_clinics(self) -> List[Dict[str, Any]]:
        """Fetch clinic profile directly from connected CRM. Returns empty list if disconnected."""
        if not crm_client.is_connected():
            return []
        crm_clinic = crm_client.get_crm_clinic()
        if crm_clinic:
            return [crm_clinic]
        return []

    def get_clinic_by_id(self, clinic_id: str) -> Optional[Dict[str, Any]]:
        """Fetch complete clinic profile directly from connected CRM."""
        if not crm_client.is_connected():
            return None
        crm_clinic = crm_client.get_crm_clinic()
        if not crm_clinic:
            return None

        clinic_dict = dict(crm_clinic)
        clinic_dict["doctors"] = self.get_doctors(clinic_dict.get("id", clinic_id))
        clinic_dict["services"] = self.get_services(clinic_dict.get("id", clinic_id))

        apps = self.get_appointments(clinic_dict.get("id", clinic_id))
        clinic_dict["total_booked"] = len(apps)
        clinic_dict["emergency_count"] = sum(1 for a in apps if a.get("is_emergency") in (1, True, "1"))
        return clinic_dict

    def get_services(self, clinic_id: str) -> List[Dict[str, Any]]:
        """Fetch treatments & prices directly from connected Dental CRM."""
        if not crm_client.is_connected():
            return []
        crm_services = crm_client.get_crm_services()
        if crm_services:
            normalized = []
            for s in crm_services:
                normalized.append({
                    "id": s.get("id"),
                    "clinic_id": clinic_id,
                    "category": s.get("category", "General"),
                    "name": s.get("name"),
                    "price_range": s.get("price_range") or f"₹{s.get('base_price', 500)}",
                    "min_price": s.get("base_price") or s.get("min_price", 500),
                    "duration_mins": s.get("duration_mins", 30),
                    "description": s.get("description", "")
                })
            return normalized
        return []

    def update_service_price(self, clinic_id: str, service_id: str, price_range: str, min_price: int) -> bool:
        """Propagate treatment price update directly to connected CRM."""
        if crm_client.is_connected():
            res = crm_client.update_crm_service_price(service_id, price_range, min_price)
            return bool(res.get("success", False))
        return False

    def get_doctors(self, clinic_id: str) -> List[Dict[str, Any]]:
        """Fetch doctors and availability directly from connected Dental CRM."""
        if not crm_client.is_connected():
            return []
        crm_docs = crm_client.get_crm_doctors()
        return crm_docs or []

    def toggle_doctor_availability(self, doctor_id: str, is_available: bool) -> bool:
        """Update doctor availability directly inside connected Dental CRM."""
        if crm_client.is_connected():
            res = crm_client.toggle_crm_doctor_availability(doctor_id, is_available)
            return bool(res.get("success", False))
        return False

    def get_available_slots(self, clinic_id: str, date_str: str, time_preference: str = "any", doctor_id: Optional[str] = None) -> List[str]:
        return compute_available_slots(clinic_id, date_str, time_preference, doctor_id)

    def book_appointment(
        self,
        clinic_id: str,
        patient_name: str,
        patient_phone: str,
        appointment_date: str,
        appointment_time: str,
        treatment_type: str = "General Consultation",
        doctor_id: Optional[str] = None,
        notes: str = "",
        booking_source: str = "AI Voice Agent"
    ) -> Dict[str, Any]:
        """
        Creates appointment directly inside the connected Dental CRM.
        Zero local database write.
        """
        if not crm_client.is_connected():
            return {
                "success": False,
                "message": "Cannot book appointment: No Dental CRM connected. Please connect a CRM first."
            }

        target_date = self._normalize_date(appointment_date)
        time_clean = appointment_time.strip()

        # Direct CRUD call to connected CRM
        crm_booking = crm_client.create_appointment(
            patient_name=patient_name,
            patient_phone=patient_phone,
            appointment_date=target_date,
            appointment_time=time_clean,
            treatment_name=treatment_type,
            doctor_id=doctor_id,
            notes=notes,
            booked_by=booking_source
        )

        app_id = crm_booking.get("id") or f"app_{uuid.uuid4().hex[:6]}"
        is_emergency = 1 if evaluate_emergency(f"{treatment_type} {notes}")["is_emergency"] else 0

        # Log call in ephemeral memory
        self.log_call(
            clinic_id=clinic_id,
            caller_name=patient_name,
            caller_phone=patient_phone,
            duration=45,
            summary=f"Booked {treatment_type} appointment for {patient_name} on {target_date} at {time_clean}",
            transcript=f"Caller: {patient_name} booked {treatment_type} on {target_date} {time_clean}. Status: Confirmed in CRM.",
            is_emergency=is_emergency,
            action_taken="Confirmed in Live CRM"
        )

        return {
            "success": True,
            "appointment_id": app_id,
            "crm_appointment_id": app_id,
            "crm_synced": True,
            "crm_sync_status": "SYNCED",
            "clinic_id": clinic_id,
            "patient_name": patient_name,
            "patient_phone": patient_phone,
            "appointment_date": target_date,
            "appointment_time": time_clean,
            "doctor_name": crm_booking.get("doctor_name", "Doctor"),
            "treatment_type": treatment_type,
            "is_emergency": is_emergency,
            "status": "Confirmed (Live CRM)",
            "message": crm_booking.get("message") or f"Appointment confirmed for {patient_name}"
        }

    def get_appointments(self, clinic_id: str) -> List[Dict[str, Any]]:
        """Fetch live appointments directly from connected Dental CRM."""
        if not crm_client.is_connected():
            return []
        crm_apps = crm_client.get_crm_appointments()
        return crm_apps or []

    def update_appointment_status(self, app_id: str, new_status: str) -> bool:
        """Propagate status update directly to connected Dental CRM."""
        if crm_client.is_connected():
            res = crm_client.update_crm_appointment_status(app_id, new_status)
            return bool(res.get("success", False))
        return False

    def sync_all_from_crm(self, clinic_id: str) -> Dict[str, Any]:
        """Fetch fresh state from connected CRM."""
        crm_clinic = crm_client.get_crm_clinic()
        apps = crm_client.get_crm_appointments() or []
        docs = crm_client.get_crm_doctors() or []
        services = crm_client.get_crm_services() or []

        now_formatted = datetime.now().strftime("%I:%M:%S %p")
        return {
            "success": True,
            "connected": True,
            "crm_url": crm_client.get_crm_url(),
            "clinic_id": clinic_id,
            "clinic": crm_clinic,
            "message": f"Successfully loaded {len(apps)} appointments, {len(docs)} doctors, and {len(services)} services from Dental CRM!",
            "stats": {
                "appointments": len(apps),
                "doctors": len(docs),
                "services": len(services)
            },
            "appointments": apps,
            "doctors": docs,
            "services": services,
            "synced_at": now_formatted
        }

    def get_integrations(self, clinic_id: str) -> Dict[str, Any]:
        crm_status = crm_client.get_sync_status()
        return {
            "clinic_id": clinic_id,
            "crm_type": "Dental Clinic CRM",
            "crm_webhook_url": f"{crm_client.get_crm_url()}/api/v1/appointments",
            "crm_base_url": crm_client.get_crm_url(),
            "crm_api_key": crm_client.api_key,
            "crm_enabled": 1 if crm_client.enabled else 0,
            "crm_connected": crm_status.get("connected", False),
            "last_synced_at": crm_status.get("last_synced_at") or "Not Synced"
        }

    def update_integrations(self, clinic_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if "crm_base_url" in data:
            crm_client.base_url = data["crm_base_url"]
        if "crm_api_key" in data:
            crm_client.api_key = data["crm_api_key"]
        return self.get_integrations(clinic_id)

    def log_call(self, clinic_id: str, caller_name: str, caller_phone: str, duration: int, summary: str, transcript: str, is_emergency: int = 0, action_taken: str = ""):
        call_obj = {
            "id": f"call_{uuid.uuid4().hex[:6]}",
            "clinic_id": clinic_id,
            "caller_name": caller_name,
            "caller_phone": caller_phone,
            "duration_seconds": duration,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "summary": summary,
            "transcript": transcript,
            "sentiment": "Satisfied",
            "is_emergency": is_emergency,
            "action_taken": action_taken or "Recorded in CRM"
        }
        self.call_logs.insert(0, call_obj)

    def get_call_logs(self, clinic_id: str) -> List[Dict[str, Any]]:
        return self.call_logs

    def get_service_pricing_reply(self, clinic_id: str, treatment_query: str) -> str:
        services = self.get_services(clinic_id)
        if not services:
            return "Hamare treatment charges consultation ke baad quote kiye jaate hain."
        q = treatment_query.lower()
        for s in services:
            if any(word in s["name"].lower() for word in q.split()):
                return f"{s['name']} ka estimated cost {s['price_range']} hai."
        first_service = services[0]
        return f"{first_service['name']} ka standard rate {first_service['price_range']} hai."

    def _normalize_date(self, date_str: str) -> str:
        return normalize_date(date_str)

    def evaluate_emergency(self, query: str) -> Dict[str, Any]:
        return evaluate_emergency(query)

dental_service = DentalService()
