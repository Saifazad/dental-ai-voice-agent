import time
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from app.core.config import settings

class DentalCrmClient:
    """
    Dedicated Gateway Client for interacting with Dental Clinic CRM (Next.js + PostgreSQL).
    Supports API Key authentication, real-time two-way synchronization,
    and automatic graceful fallback to local SQLite cache if CRM is offline.
    """
    def __init__(self):
        self.base_url = settings.DENTAL_CRM_BASE_URL
        self.api_key = settings.DENTAL_CRM_API_KEY
        self.enabled = settings.DENTAL_CRM_ENABLED
        self.timeout = settings.DENTAL_CRM_TIMEOUT_SECONDS

        self.connected = False
        self.last_sync_time: Optional[str] = None
        self.last_stats = {"appointments": 0, "doctors": 0, "services": 0}

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.api_key and self.api_key.strip():
            clean_key = self.api_key.strip()
            headers["Authorization"] = f"Bearer {clean_key}"
            headers["x-api-key"] = clean_key
        return headers

    def configure(self, base_url: str, api_key: Optional[str] = None, enabled: bool = True) -> Dict[str, Any]:
        """Dynamically update CRM connection settings and verify handshake."""
        if base_url:
            self.base_url = str(base_url).strip().rstrip("/")
        if api_key is not None:
            self.api_key = str(api_key).strip()
        self.enabled = bool(enabled)

        # Immediate health check / handshake
        health = self.check_health()
        self.connected = bool(health.get("online"))
        return {
            "success": self.connected,
            "connected": self.connected,
            "crm_url": self.base_url,
            "api_key_configured": bool(self.api_key),
            "diagnostics": health
        }

    def _normalize_date(self, date_str: str) -> str:
        if not date_str:
            return datetime.now().strftime("%Y-%m-%d")
        d = str(date_str).lower().strip()
        if d in ("today", "aaj"):
            return datetime.now().strftime("%Y-%m-%d")
        elif d in ("tomorrow", "kal"):
            return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        elif d in ("day after tomorrow", "parso"):
            return (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        return date_str

    def get_crm_url(self) -> str:
        return self.base_url

    def is_connected(self) -> bool:
        return self.enabled and self.connected

    def check_health(self) -> Dict[str, Any]:
        """Check if Dental Clinic CRM server is alive and responding."""
        if not self.enabled:
            return {"online": False, "reason": "CRM sync disabled via config"}

        # Try clinic endpoint first
        url = f"{self.base_url}/api/v1/clinic"
        headers = self._get_headers()
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.get(url, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    self.connected = True
                    return {
                        "online": True,
                        "status_code": 200,
                        "crm_url": self.base_url,
                        "clinic": data.get("clinic", {}),
                        "message": "Dental Clinic CRM (PostgreSQL) is ONLINE and responding"
                    }
                elif res.status_code in (401, 403):
                    return {
                        "online": False,
                        "status_code": res.status_code,
                        "crm_url": self.base_url,
                        "message": "CRM responded with 401/403: Invalid or Missing API Key"
                    }
        except Exception:
            pass

        # Fallback ping via availability endpoint
        avail_url = f"{self.base_url}/api/v1/availability"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.get(avail_url, params={"date": "today"}, headers=headers)
                if res.status_code == 200:
                    self.connected = True
                    return {
                        "online": True,
                        "status_code": 200,
                        "crm_url": self.base_url,
                        "message": "Dental Clinic CRM is ONLINE and responding"
                    }
                else:
                    return {
                        "online": False,
                        "status_code": res.status_code,
                        "crm_url": self.base_url,
                        "message": f"CRM responded with HTTP {res.status_code}"
                    }
        except httpx.ConnectError:
            self.connected = False
            return {
                "online": False,
                "crm_url": self.base_url,
                "message": f"Cannot connect to CRM at {self.base_url}. Ensure dental-clinic-crm is running on port 3000."
            }
        except httpx.TimeoutException:
            self.connected = False
            return {
                "online": False,
                "crm_url": self.base_url,
                "message": f"Connection to CRM timed out after {self.timeout}s"
            }
        except Exception as e:
            self.connected = False
            return {
                "online": False,
                "crm_url": self.base_url,
                "message": f"CRM check error: {str(e)}"
            }

    def get_crm_clinic(self) -> Optional[Dict[str, Any]]:
        """Fetch clinic profile from Dental Clinic CRM (PostgreSQL)."""
        if not self.enabled:
            return None
        url = f"{self.base_url}/api/v1/clinic"
        headers = self._get_headers()
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.get(url, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    return data.get("clinic")
        except Exception:
            return None
        return None

    def get_crm_appointments(self) -> Optional[List[Dict[str, Any]]]:
        """Fetch all live appointments from Dental Clinic CRM (PostgreSQL)."""
        if not self.enabled:
            return None

        url = f"{self.base_url}/api/v1/appointments"
        headers = self._get_headers()
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.get(url, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    raw_apps = data.get("appointments", [])
                    normalized = []
                    for item in raw_apps:
                        normalized.append({
                            "id": item.get("id"),
                            "clinic_id": item.get("clinic_id", "clinic_bangalore"),
                            "patient_name": item.get("patient_name", "Unknown Patient"),
                            "patient_phone": item.get("patient_phone", ""),
                            "appointment_date": item.get("appointment_date", "Today"),
                            "appointment_time": item.get("appointment_time", "10:00 AM"),
                            "treatment_type": item.get("treatment_name") or item.get("treatment_type", "General Consultation"),
                            "doctor_id": item.get("doctor_id"),
                            "doctor_name": item.get("doctor_name", "Dr. Alok Aggarwal"),
                            "status": item.get("status", "Confirmed"),
                            "is_emergency": 1 if item.get("is_emergency") in (1, True, "1") else 0,
                            "booking_source": item.get("booked_by") or item.get("booking_source", "Dental CRM (PostgreSQL)"),
                            "notes": item.get("notes", ""),
                            "created_at": item.get("created_at") or datetime.now().isoformat(),
                            "crm_appointment_id": item.get("id"),
                            "crm_synced": 1,
                            "crm_sync_status": "SYNCED"
                        })
                    self.connected = True
                    self.last_sync_time = datetime.now().strftime("%I:%M:%S %p")
                    self.last_stats["appointments"] = len(normalized)
                    return normalized
        except Exception as e:
            print(f"⚠️ [CRM Client] Fetch appointments error: {e}")

        return None

    def update_crm_appointment_status(self, app_id: str, new_status: str) -> Dict[str, Any]:
        """Update appointment status inside Dental Clinic CRM (PostgreSQL)."""
        if not self.enabled:
            return {"success": False, "offline": True}

        url = f"{self.base_url}/api/v1/appointments"
        headers = self._get_headers()
        payload = {"id": app_id, "status": new_status}
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.patch(url, json=payload, headers=headers)
                if res.status_code == 200:
                    return {"success": True, "crm_updated": True}
                return {"success": False, "status_code": res.status_code}
        except Exception as e:
            print(f"⚠️ [CRM Client] Update appointment status error: {e}")
            return {"success": False, "error": str(e)}

    def get_crm_doctors(self) -> Optional[List[Dict[str, Any]]]:
        """Fetch all doctors and availability from Dental Clinic CRM (PostgreSQL)."""
        if not self.enabled:
            return None

        url = f"{self.base_url}/api/v1/doctors"
        headers = self._get_headers()
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.get(url, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    docs = data.get("doctors", [])
                    self.last_stats["doctors"] = len(docs)
                    return docs
        except Exception as e:
            print(f"⚠️ [CRM Client] Fetch doctors error: {e}")

        return None

    def toggle_crm_doctor_availability(self, doctor_id: str, is_available: bool) -> Dict[str, Any]:
        """Toggle doctor shift/availability in CRM."""
        if not self.enabled:
            return {"success": False, "offline": True}

        url = f"{self.base_url}/api/v1/doctors"
        headers = self._get_headers()
        payload = {"id": doctor_id, "is_available": 1 if is_available else 0}
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.patch(url, json=payload, headers=headers)
                if res.status_code == 200:
                    return {"success": True}
                return {"success": False, "status_code": res.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_crm_services(self) -> Optional[List[Dict[str, Any]]]:
        """Fetch live services and pricing from Dental Clinic CRM."""
        if not self.enabled:
            return None

        url = f"{self.base_url}/api/v1/services"
        headers = self._get_headers()
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.get(url, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    services = data.get("services", [])
                    self.last_stats["services"] = len(services)
                    return services
        except Exception as e:
            print(f"⚠️ [CRM Client] Services fetch error: {e}")

        return None

    def update_crm_service_price(self, service_id: str, price_range: str, min_price: int) -> Dict[str, Any]:
        """Update treatment price inside Dental CRM."""
        if not self.enabled:
            return {"success": False, "offline": True}

        url = f"{self.base_url}/api/v1/services"
        headers = self._get_headers()
        payload = {"id": service_id, "price_range": price_range, "base_price": min_price}
        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.put(url, json=payload, headers=headers)
                if res.status_code == 200:
                    return {"success": True}
                return {"success": False, "status_code": res.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_crm_availability(self, date: str, time_pref: str = "any", doctor_id: Optional[str] = None) -> Optional[List[str]]:
        """Fetch live available slots directly from Dental Clinic CRM's PostgreSQL database."""
        return self.get_availability(date_str=date, time_preference=time_pref, doctor_id=doctor_id)

    def get_availability(self, date_str: str, time_preference: str = "any", doctor_id: Optional[str] = None) -> Optional[List[str]]:
        """Fetch live available slots directly from Dental Clinic CRM's PostgreSQL database."""
        if not self.enabled:
            return None

        url = f"{self.base_url}/api/v1/availability"
        headers = self._get_headers()
        params = {"date": self._normalize_date(date_str), "time_preference": time_preference}
        if doctor_id:
            params["doctor_id"] = doctor_id

        for attempt in range(2):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    res = client.get(url, params=params, headers=headers)
                    if res.status_code == 200:
                        data = res.json()
                        if data.get("success") and "available_slots" in data:
                            return data["available_slots"]
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                if attempt == 0:
                    time.sleep(0.15)
                    continue
                print(f"⚠️ [CRM Client] Availability check fallback to local: {e}")
            except Exception as e:
                print(f"⚠️ [CRM Client] Unexpected availability error: {e}")
                break

        return None

    def create_appointment(
        self,
        patient_name: str,
        patient_phone: str,
        appointment_date: str,
        appointment_time: str,
        treatment_name: str = "General Consultation",
        doctor_id: Optional[str] = None,
        notes: str = "",
        booked_by: str = "AI Voice Receptionist (Vapi)"
    ) -> Dict[str, Any]:
        """Create appointment inside Dental Clinic CRM's PostgreSQL database with retry."""
        if not self.enabled:
            return {
                "success": False,
                "offline": True,
                "message": "CRM sync is disabled in config"
            }

        url = f"{self.base_url}/api/v1/appointments"
        headers = self._get_headers()
        payload = {
            "patient_name": patient_name,
            "patient_phone": patient_phone,
            "appointment_date": self._normalize_date(appointment_date),
            "appointment_time": appointment_time,
            "treatment_name": treatment_name,
            "notes": notes,
            "booked_by": booked_by
        }
        if doctor_id:
            payload["doctor_id"] = doctor_id

        for attempt in range(2):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    res = client.post(url, json=payload, headers=headers)
                    if res.status_code == 200:
                        return res.json()
                    elif res.status_code == 400:
                        data = res.json()
                        return {
                            "success": False,
                            "conflict": data.get("conflict", False),
                            "message": data.get("message", "Validation error from CRM")
                        }
                    else:
                        return {
                            "success": False,
                            "offline": True,
                            "message": f"CRM server error HTTP {res.status_code}"
                        }
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                if attempt == 0:
                    time.sleep(0.2)
                    continue
                return {
                    "success": False,
                    "offline": True,
                    "message": f"Could not connect to Dental CRM at {self.base_url} ({type(e).__name__})"
                }
            except Exception as e:
                return {
                    "success": False,
                    "offline": True,
                    "message": f"CRM error: {str(e)}"
                }

        return {"success": False, "offline": True, "message": "Failed after retries"}

    def get_sync_status(self) -> Dict[str, Any]:
        return {
            "connected": self.connected,
            "crm_url": self.base_url,
            "api_key_configured": bool(self.api_key),
            "api_key_masked": f"{self.api_key[:4]}••••••••{self.api_key[-3:]}" if len(self.api_key) > 7 else ("••••" if self.api_key else ""),
            "last_synced_at": self.last_sync_time or "Never",
            "stats": self.last_stats
        }

# Singleton instance
crm_client = DentalCrmClient()
