from fastapi import APIRouter
from app.services.dental_service import dental_service
from app.schemas.simulation import VoiceSimulationRequest

router = APIRouter(prefix="/api", tags=["Demo Simulation"])

@router.post("/simulate-call")
def simulate_voice_call(req: VoiceSimulationRequest):
    """
    Executes an end-to-end voice scenario, running real database queries,
    generating natural Hinglish AI audio response text, and updating the database!
    """
    req.clinic_id = dental_service.resolve_clinic_id(req.clinic_id)
    clinic = dental_service.get_clinic_by_id(req.clinic_id)

    assistant_name = clinic.get("assistant_name", "Aanya") if clinic else "Aanya"
    clinic_name = clinic.get("name", "Dental Clinic") if clinic else "Dental Clinic"

    scenario = req.scenario.lower()

    if "pricing" in scenario or "scaling" in scenario or "rate" in scenario:
        reply = dental_service.get_service_pricing_reply(req.clinic_id, "cleaning scaling")
        transcript = [
            {"role": "user", "text": "Namaste, mujhe daanto ki safai aur scaling karwani hai. Kitna kharcha aayega?"},
            {"role": "assistant", "text": f"Namaste! {clinic_name} me aapka swagat hai. Main {assistant_name} bol rahi hu. {reply} Kya main aapke liye ek convenient appointment schedule kar du?"}
        ]
        return {
            "scenario": "Pricing Inquiry",
            "assistant_name": assistant_name,
            "tool_executed": "get_service_pricing",
            "db_action": "Fetched custom treatment rates from SQLite DB",
            "spoken_text": transcript[1]["text"],
            "transcript": transcript,
            "appointment_created": False
        }

    elif "emergency" in scenario or "bleeding" in scenario or "pain" in scenario:
        triage = dental_service.evaluate_emergency("severe unbearable pain bleeding")
        # Auto-reserve emergency slot
        res = dental_service.book_appointment(
            clinic_id=req.clinic_id,
            patient_name=req.patient_name or "Emergency Patient",
            patient_phone=req.patient_phone or "+91 98888 11111",
            appointment_date="today",
            appointment_time="11:45 AM",
            treatment_type="Acute Dental Emergency (Pain/Bleeding)",
            notes="Patient reported severe acute bleeding and throbbing pain. Priority triage flagged.",
            booking_source="AI Voice Agent"
        )
        city_name = clinic.get("city", "our") if clinic else "our"
        ai_reply = f"Yeh emergency situation lag rahi hai. Maine turant hamare on-call doctor ko alert bhej diya hai aur aapke liye priority emergency slot reserve kar diya hai. Kripya bina deri kiye turant {city_name} clinic visit karein."
        transcript = [
            {"role": "user", "text": "Doctor sahab, mere daant se bahut khoon nikal raha hai aur bahut tez unbearable dard hai!"},
            {"role": "assistant", "text": f"Ghabraiye mat! Main {assistant_name} bol rahi hu {clinic_name} se. {ai_reply}"}
        ]
        return {
            "scenario": "Emergency Triage",
            "assistant_name": assistant_name,
            "tool_executed": "check_emergency & book_appointment",
            "db_action": "Emergency appointment locked in SQLite DB + Priority Alert triggered",
            "spoken_text": ai_reply,
            "transcript": transcript,
            "appointment_created": True,
            "appointment": res
        }

    elif "slots" in scenario or "availability" in scenario:
        open_slots = dental_service.get_available_slots(req.clinic_id, "tomorrow", "evening")
        slots_str = ", ".join(open_slots[:3])
        ai_reply = f"Kal shaam ke liye hamare paas {slots_str} available hain. Aapke liye kaunsa time theek rahega?"
        transcript = [
            {"role": "user", "text": "Mujhe kal shaam ko aana hai, kya koi slot khali hai?"},
            {"role": "assistant", "text": f"Haan bilkul! {clinic_name} me kal ke liye {ai_reply}"}
        ]
        return {
            "scenario": "Check Availability",
            "assistant_name": assistant_name,
            "tool_executed": "check_availability",
            "db_action": "Calculated real unbooked slots from SQLite schedule",
            "spoken_text": ai_reply,
            "transcript": transcript,
            "appointment_created": False
        }

    else:
        # Default: Book Root Canal or Consultation
        treatment = "Root Canal Treatment (RCT)"
        open_slots = dental_service.get_available_slots(req.clinic_id, "tomorrow", "morning")
        slot_time = open_slots[0] if open_slots else "11:15 AM"

        res = dental_service.book_appointment(
            clinic_id=req.clinic_id,
            patient_name=req.patient_name or "Amitabh Mehra",
            patient_phone=req.patient_phone or "+91 99301 22849",
            appointment_date="tomorrow",
            appointment_time=slot_time,
            treatment_type=treatment,
            notes="Booked via AI Voice Live Demo. Patient requested painless RCT specialist.",
            booking_source="AI Voice Agent"
        )

        crm_ref = res.get("crm_appointment_id")
        crm_synced = res.get("crm_synced", False)
        crm_tag = f" CRM Reference ID: {crm_ref}." if crm_ref else ""
        ai_reply = f"Bahut badhiya! {req.patient_name or 'Amitabh ji'}, aapka {treatment} ka appointment kal {slot_time} par {clinic_name} me successfully book ho gaya hai.{crm_tag} Doctor ko notify kar diya hai aur confirmation SMS bhej diya gaya hai."
        transcript = [
            {"role": "user", "text": f"Mujhe kal {treatment} karwana hai, mera naam {req.patient_name or 'Amitabh Mehra'} hai."},
            {"role": "assistant", "text": f"Ji bilkul. {ai_reply}"}
        ]
        return {
            "scenario": "Appointment Booking",
            "assistant_name": assistant_name,
            "tool_executed": "book_appointment",
            "db_action": f"Appointment synced to Dental Clinic CRM (ID: {crm_ref}) + Local DB mirror" if crm_synced else "Appointment saved to local DB (CRM offline fallback)",
            "crm_synced": crm_synced,
            "crm_appointment_id": crm_ref,
            "spoken_text": ai_reply,
            "transcript": transcript,
            "appointment_created": True,
            "appointment": res
        }
