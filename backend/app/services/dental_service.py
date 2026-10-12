import uuid
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from app.db.connection import get_connection
from app.integrations.crm_client import crm_client
from app.services.triage_service import evaluate_emergency, EMERGENCY_KEYWORDS
from app.services.slot_service import get_available_slots as compute_available_slots, normalize_date

class DentalService:
    def _upsert_crm_clinic(self, crm_clinic: Dict[str, Any]) -> str:
        cid = crm_clinic.get("id") or "clinic_001"
        name = crm_clinic.get("name", "Dental Clinic")
        city = crm_clinic.get("city", "")
        address = crm_clinic.get("address", "")
        phone = crm_clinic.get("phone", "")
        opening = crm_clinic.get("opening_time", "10:00 AM")
        closing = crm_clinic.get("closing_time", "08:30 PM")
        lunch_start = crm_clinic.get("lunch_start", "01:30 PM")
        lunch_end = crm_clinic.get("lunch_end", "02:30 PM")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO clinics (
            id, name, city, address, phone_number, emergency_phone,
            assistant_name, assistant_tone, opening_time, closing_time, lunch_start, lunch_end
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name = excluded.name,
            city = excluded.city,
            address = excluded.address,
            phone_number = excluded.phone_number,
            opening_time = excluded.opening_time,
            closing_time = excluded.closing_time,
            lunch_start = excluded.lunch_start,
            lunch_end = excluded.lunch_end
        """, (
            cid, name, city, address, phone, phone,
            "Aanya", "Warm, Reassuring & Polite (Hindi & English)",
            opening, closing, lunch_start, lunch_end
        ))

        cursor.execute("""
        INSERT INTO clinic_integrations (
            clinic_id, google_sheets_enabled, google_sheet_url, google_sheet_id,
            google_calendar_enabled, google_calendar_email, crm_type, crm_webhook_url,
            crm_base_url, crm_enabled, whatsapp_enabled, last_synced_at, crm_status, crm_api_key
        ) VALUES (?, 0, '', '', 0, '', 'Dental Clinic CRM', ?, ?, 1, 0, ?, 'Connected', ?)
        ON CONFLICT(clinic_id) DO UPDATE SET
            crm_base_url = excluded.crm_base_url,
            crm_webhook_url = excluded.crm_webhook_url,
            crm_status = excluded.crm_status,
            crm_enabled = 1,
            last_synced_at = excluded.last_synced_at
        """, (
            cid,
            f"{crm_client.get_crm_url()}/api/v1/appointments",
            crm_client.get_crm_url(),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            crm_client.api_key
        ))
        conn.commit()
        conn.close()
        return cid

    def resolve_clinic_id(self, clinic_id: Optional[str] = None) -> str:
        if clinic_id and clinic_id not in ("clinic_bangalore", "default", "null", "undefined"):
            return clinic_id
        clinics = self.get_clinics()
        if clinics:
            return clinics[0]["id"]
        return "clinic_001"

    def get_clinics(self) -> List[Dict[str, Any]]:
        if crm_client.is_connected() or crm_client.enabled:
            crm_clinic = crm_client.get_crm_clinic()
            if crm_clinic:
                self._upsert_crm_clinic(crm_clinic)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clinics ORDER BY name ASC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_clinic_by_id(self, clinic_id: str) -> Optional[Dict[str, Any]]:
        cid = clinic_id
        if crm_client.is_connected() or crm_client.enabled:
            crm_clinic = crm_client.get_crm_clinic()
            if crm_clinic:
                cid = self._upsert_crm_clinic(crm_clinic)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clinics WHERE id = ?", (cid,))
        clinic = cursor.fetchone()
        if not clinic:
            cursor.execute("SELECT * FROM clinics LIMIT 1")
            clinic = cursor.fetchone()
            if not clinic:
                conn.close()
                return None
        clinic_dict = dict(clinic)

        # Fetch doctors (Live from CRM if online)
        clinic_dict["doctors"] = self.get_doctors(clinic_dict["id"])

        # Fetch services (Live from CRM if online)
        clinic_dict["services"] = self.get_services(clinic_dict["id"])

        # Quick stats from appointments
        apps = self.get_appointments(clinic_dict["id"])
        clinic_dict["total_booked"] = len(apps)
        clinic_dict["emergency_count"] = sum(1 for a in apps if a.get("is_emergency") in (1, True, "1"))

        conn.close()
        return clinic_dict

    def get_services(self, clinic_id: str) -> List[Dict[str, Any]]:
        """Fetch treatments & prices. Tries live Dental CRM first, falls back to SQLite."""
        if crm_client.is_connected() or crm_client.enabled:
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

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM services WHERE clinic_id = ? ORDER BY min_price ASC", (clinic_id,))
        services = [dict(s) for s in cursor.fetchall()]
        conn.close()
        return services

    def update_service_price(self, clinic_id: str, service_id: str, price_range: str, min_price: int) -> bool:
        # Update local SQLite
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE services 
        SET price_range = ?, min_price = ? 
        WHERE id = ? AND clinic_id = ?
        """, (price_range, min_price, service_id, clinic_id))
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()

        # Update in CRM if connected
        if crm_client.is_connected() or crm_client.enabled:
            crm_client.update_crm_service_price(service_id, price_range, min_price)

        return updated

    def get_doctors(self, clinic_id: str) -> List[Dict[str, Any]]:
        """Fetch doctors. Queries live Dental CRM first, falls back to SQLite."""
        if crm_client.is_connected() or crm_client.enabled:
            crm_docs = crm_client.get_crm_doctors()
            if crm_docs:
                return crm_docs

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM doctors WHERE clinic_id = ?", (clinic_id,))
        doctors = [dict(d) for d in cursor.fetchall()]
        conn.close()
        return doctors

    def toggle_doctor_availability(self, doctor_id: str, is_available: bool) -> bool:
        # Update local SQLite
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE doctors SET is_available = ? WHERE id = ?", (1 if is_available else 0, doctor_id))
        conn.commit()
        conn.close()

        # Update CRM
        if crm_client.is_connected() or crm_client.enabled:
            crm_client.toggle_crm_doctor_availability(doctor_id, is_available)

        return True

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
        Create appointment with TWO-WAY synchronization:
        1. Directly pushes into Dental Clinic CRM's PostgreSQL database.
        2. Mirrors into local SQLite database for instant dashboard caching & offline resilience.
        """
        target_date = self._normalize_date(appointment_date)
        time_clean = appointment_time.strip()

        # 1. Attempt Booking into Dental Clinic CRM (PostgreSQL)
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

        crm_app_id = None
        crm_sync_status = "LOCAL_ONLY"
        doctor_name = "Dr. Alok Aggarwal"

        if crm_booking.get("success"):
            crm_app_id = crm_booking.get("appointment_id")
            crm_sync_status = "SYNCED"
            doctor_name = crm_booking.get("doctor_name", doctor_name)
        elif crm_booking.get("conflict"):
            return {
                "success": False,
                "conflict": True,
                "message": crm_booking.get("message", "Slot is already booked in Dental CRM.")
            }

        # 2. Mirror into Local SQLite Database
        app_id = crm_app_id or f"app_{uuid.uuid4().hex[:8]}"
        is_emergency = 1 if any(kw in f"{treatment_type} {notes}".lower() for kw in EMERGENCY_KEYWORDS) else 0

        conn = get_connection()
        cursor = conn.cursor()

        if not doctor_id:
            cursor.execute("SELECT id, name FROM doctors WHERE clinic_id = ? AND is_available = 1 LIMIT 1", (clinic_id,))
            doc_row = cursor.fetchone()
            if doc_row:
                doctor_id = doc_row["id"]
                doctor_name = doc_row["name"]

        cursor.execute("""
        INSERT OR REPLACE INTO appointments (
            id, clinic_id, doctor_id, doctor_name, patient_name, patient_phone,
            appointment_date, appointment_time, treatment_type, status,
            is_emergency, notes, booking_source, crm_appointment_id, crm_sync_status, crm_synced_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            app_id,
            clinic_id,
            doctor_id,
            doctor_name,
            patient_name,
            patient_phone,
            target_date,
            time_clean,
            treatment_type,
            "Confirmed (AI Voice)",
            is_emergency,
            notes,
            booking_source,
            crm_app_id,
            crm_sync_status,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()

        # Log Call entry if booked via voice
        if "Voice" in booking_source:
            call_id = f"call_{uuid.uuid4().hex[:8]}"
            cursor.execute("""
            INSERT INTO call_logs (
                id, clinic_id, caller_name, caller_phone, duration_seconds,
                timestamp, summary, transcript, sentiment, is_emergency, action_taken
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                call_id,
                clinic_id,
                patient_name,
                patient_phone,
                48,
                "Just Now",
                f"Voice call with {patient_name} for {treatment_type}. Slot confirmed at {time_clean} ({target_date}).",
                f"Caller requested appointment. AI checked availability, locked slot {time_clean}, and synced with CRM.",
                "Satisfied",
                is_emergency,
                "Appointment Booked in CRM" if crm_app_id else "Appointment Booked"
            ))
            conn.commit()

        conn.close()

        return {
            "success": True,
            "appointment_id": app_id,
            "crm_appointment_id": crm_app_id,
            "crm_synced": True if crm_sync_status == "SYNCED" else False,
            "crm_sync_status": crm_sync_status,
            "clinic_id": clinic_id,
            "patient_name": patient_name,
            "patient_phone": patient_phone,
            "appointment_date": target_date,
            "appointment_time": time_clean,
            "doctor_name": doctor_name,
            "treatment_type": treatment_type,
            "is_emergency": is_emergency,
            "status": "Confirmed (AI Voice)",
            "message": crm_booking.get("message") or f"Appointment confirmed for {patient_name}"
        }

    def get_appointments(self, clinic_id: str) -> List[Dict[str, Any]]:
        """
        Dynamically fetches appointments:
        1. Checks Dental Clinic CRM (PostgreSQL) live.
        2. Mirrors rows into local SQLite.
        3. If CRM offline, returns local SQLite cache.
        """
        if crm_client.is_connected() or crm_client.enabled:
            crm_apps = crm_client.get_crm_appointments()
            if crm_apps is not None:
                # Mirror to SQLite cache
                conn = get_connection()
                cursor = conn.cursor()
                for app in crm_apps:
                    cursor.execute("""
                    INSERT INTO appointments (
                        id, clinic_id, doctor_id, doctor_name, patient_name, patient_phone,
                        appointment_date, appointment_time, treatment_type, status,
                        is_emergency, notes, booking_source, created_at, crm_appointment_id, crm_sync_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        doctor_id=excluded.doctor_id,
                        doctor_name=excluded.doctor_name,
                        patient_name=excluded.patient_name,
                        patient_phone=excluded.patient_phone,
                        appointment_date=excluded.appointment_date,
                        appointment_time=excluded.appointment_time,
                        treatment_type=excluded.treatment_type,
                        status=excluded.status,
                        is_emergency=excluded.is_emergency,
                        notes=excluded.notes,
                        crm_sync_status='SYNCED'
                    """, (
                        app.get("id"),
                        clinic_id,
                        app.get("doctor_id"),
                        app.get("doctor_name"),
                        app.get("patient_name"),
                        app.get("patient_phone"),
                        app.get("appointment_date"),
                        app.get("appointment_time"),
                        app.get("treatment_type"),
                        app.get("status"),
                        app.get("is_emergency", 0),
                        app.get("notes", ""),
                        app.get("booking_source", "Dental CRM (PostgreSQL)"),
                        app.get("created_at"),
                        app.get("id"),
                        "SYNCED"
                    ))
                conn.commit()
                conn.close()
                return crm_apps

        # Fallback to local SQLite if CRM is offline - only return real CRM-synced records
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM appointments 
        WHERE clinic_id = ? AND crm_appointment_id IS NOT NULL 
        ORDER BY created_at DESC
        """, (clinic_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def update_appointment_status(self, app_id: str, new_status: str) -> bool:
        """Updates appointment status in local DB and propagates PATCH to Dental CRM."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE appointments SET status = ? WHERE id = ?", (new_status, app_id))
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()

        # Sync with Dental Clinic CRM
        if crm_client.is_connected() or crm_client.enabled:
            crm_client.update_crm_appointment_status(app_id, new_status)

        return updated

    def get_call_logs(self, clinic_id: str) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM call_logs 
        WHERE clinic_id = ? 
        ORDER BY id DESC
        """, (clinic_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def evaluate_emergency(self, symptoms: str) -> Dict[str, Any]:
        return evaluate_emergency(symptoms)

    def get_service_pricing_reply(self, clinic_id: str, treatment_query: str) -> str:
        """Find matching service from clinic database and format AI response."""
        services = self.get_services(clinic_id)
        query = (treatment_query or "").lower()
        matched = None
        for s in services:
            s_name = s["name"].lower()
            if any(term in s_name for term in query.split()) or any(term in query for term in s_name.split()):
                matched = s
                break

        if matched:
            return f"Hamare clinic me {matched['name']} ka standard estimated price {matched['price_range']} hai. Exact procedure cost doctor physical checkup ke baad confirm karte hain."

        return "General dental consultation and digital checkup fee ₹500 - ₹700 hai. Specific treatment ki exact pricing doctor examine karne ke baad batate hain."

    def sync_all_from_crm(self, clinic_id: str) -> Dict[str, Any]:
        """Performs a comprehensive bi-directional pull from Dental Clinic CRM."""
        health = crm_client.check_health()
        if not health.get("online"):
            return {
                "success": False,
                "connected": False,
                "message": health.get("message", "CRM Offline"),
                "diagnostics": health
            }

        # 1. Sync Clinic Profile from CRM
        crm_clinic = crm_client.get_crm_clinic()
        if crm_clinic:
            clinic_id = self._upsert_crm_clinic(crm_clinic)

        apps = self.get_appointments(clinic_id)
        docs = self.get_doctors(clinic_id)
        services = self.get_services(clinic_id)

        # Mirror doctors to SQLite
        conn = get_connection()
        cursor = conn.cursor()
        for doc in docs:
            cursor.execute("""
            INSERT INTO doctors (id, clinic_id, name, qualification, specialization, experience_years, consultation_fee, is_available, working_days)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                clinic_id=excluded.clinic_id,
                name=excluded.name,
                qualification=excluded.qualification,
                specialization=excluded.specialization,
                experience_years=excluded.experience_years,
                consultation_fee=excluded.consultation_fee,
                is_available=excluded.is_available,
                working_days=excluded.working_days
            """, (
                doc.get("id"),
                clinic_id,
                doc.get("name"),
                doc.get("qualification", "BDS"),
                doc.get("specialization", "Dentist"),
                doc.get("experience_years", 10),
                doc.get("fee") or doc.get("consultation_fee", 500),
                doc.get("is_available", 1),
                doc.get("working_days", "Mon-Sat")
            ))

        # Mirror services to SQLite
        for srv in services:
            cursor.execute("""
            INSERT INTO services (id, clinic_id, category, name, price_range, min_price, duration_mins, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                clinic_id=excluded.clinic_id,
                category=excluded.category,
                name=excluded.name,
                price_range=excluded.price_range,
                min_price=excluded.min_price,
                duration_mins=excluded.duration_mins,
                description=excluded.description
            """, (
                srv.get("id"),
                clinic_id,
                srv.get("category", "General"),
                srv.get("name"),
                srv.get("price_range"),
                srv.get("min_price", 500),
                srv.get("duration_mins", 30),
                srv.get("description", "")
            ))
        conn.commit()
        conn.close()

        crm_client.last_sync_time = datetime.now().strftime("%I:%M:%S %p")
        crm_client.last_stats = {
            "appointments": len(apps),
            "doctors": len(docs),
            "services": len(services)
        }

        now_formatted = datetime.now().strftime("%I:%M:%S %p")
        return {
            "success": True,
            "connected": True,
            "crm_url": crm_client.get_crm_url(),
            "clinic_id": clinic_id,
            "clinic": crm_clinic,
            "message": f"Successfully synchronized {len(apps)} appointments, {len(docs)} doctors, and {len(services)} services from Dental CRM (PostgreSQL)!",
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
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clinic_integrations WHERE clinic_id = ?", (clinic_id,))
        row = cursor.fetchone()
        crm_status = crm_client.get_sync_status()
        if not row:
            conn.close()
            return {
                "clinic_id": clinic_id,
                "google_sheets_enabled": 0,
                "google_sheet_url": "",
                "google_sheet_id": "",
                "google_calendar_enabled": 0,
                "google_calendar_email": "",
                "crm_type": "Dental Clinic CRM",
                "crm_webhook_url": f"{crm_client.get_crm_url()}/api/v1/appointments",
                "crm_base_url": crm_client.get_crm_url(),
                "crm_api_key": crm_client.api_key,
                "crm_enabled": 1 if crm_client.enabled else 0,
                "crm_connected": crm_status["connected"],
                "whatsapp_enabled": 0,
                "last_synced_at": crm_status["last_synced_at"] or "Not Synced"
            }
        res = dict(row)
        res["crm_connected"] = crm_status["connected"]
        res["crm_base_url"] = crm_client.get_crm_url()
        res["crm_api_key"] = crm_client.api_key
        res["last_synced_at"] = crm_status["last_synced_at"] or "Not Synced"
        conn.close()
        return res

    def update_integrations(self, clinic_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        conn = get_connection()
        cursor = conn.cursor()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        crm_url = data.get("crm_base_url") or data.get("crm_webhook_url", "http://localhost:3000")
        api_key = data.get("crm_api_key", "")
        crm_enabled = bool(data.get("crm_enabled", True))

        # Re-configure CRM client dynamically
        crm_client.configure(crm_url, api_key, crm_enabled)

        cursor.execute("""
        INSERT OR REPLACE INTO clinic_integrations (
            clinic_id, google_sheets_enabled, google_sheet_url, google_sheet_id,
            google_calendar_enabled, google_calendar_email, crm_type, crm_webhook_url,
            crm_base_url, crm_enabled, whatsapp_enabled, last_synced_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            clinic_id,
            1 if data.get("google_sheets_enabled", True) else 0,
            data.get("google_sheet_url", ""),
            data.get("google_sheet_id", ""),
            1 if data.get("google_calendar_enabled", True) else 0,
            data.get("google_calendar_email", ""),
            data.get("crm_type", "Dental Clinic CRM (Desktop)"),
            f"{crm_client.get_crm_url()}/api/v1/appointments",
            crm_client.get_crm_url(),
            1 if crm_enabled else 0,
            1 if data.get("whatsapp_enabled", True) else 0,
            now_str
        ))
        conn.commit()
        conn.close()
        return self.get_integrations(clinic_id)

    def _normalize_date(self, date_str: str) -> str:
        return normalize_date(date_str)

dental_service = DentalService()
