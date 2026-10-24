import time
import json
import httpx
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from app.core.config import settings

CONFIG_FILE = Path(__file__).parent.parent / "crm_config.json"

class DentalCrmClient:
    """
    Dedicated Gateway Client for interacting with Dental Clinic CRM (Next.js + PostgreSQL).
    Supports API Key authentication, real-time two-way synchronization,
    and automatic graceful fallback to local SQLite cache if CRM is offline.
    """
    DEFAULT_ROUTES = {
        "clinic": "/api/v1/clinic",
        "appointments": "/api/v1/appointments",
        "doctors": "/api/v1/doctors",
        "services": "/api/v1/services",
        "availability": "/api/v1/availability"
    }

    def __init__(self):
        self.base_url = settings.DENTAL_CRM_BASE_URL
        self.api_key = settings.DENTAL_CRM_API_KEY
        self.enabled = settings.DENTAL_CRM_ENABLED
        self.timeout = settings.DENTAL_CRM_TIMEOUT_SECONDS

        self.connected = False
        self.last_sync_time: Optional[str] = None
        self.last_stats = {"appointments": 0, "doctors": 0, "services": 0}
        self.schema_mapping: Optional[Dict[str, str]] = None
        self.custom_routes: Dict[str, str] = dict(self.DEFAULT_ROUTES)

        # Auto-restore connection if previously saved via dashboard
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
                    saved = json.load(f)
                    if saved.get("crm_url"):
                        self.base_url = str(saved["crm_url"]).strip().rstrip("/")
                        if saved.get("api_key"):
                            self.api_key = str(saved["api_key"]).strip()
                        self.enabled = saved.get("enabled", True)
                        if saved.get("custom_routes"):
                            self.custom_routes.update(saved["custom_routes"])
                        health = self.check_health()
                        self.connected = bool(health.get("online"))
            except Exception:
                pass
        elif self.base_url:
            try:
                health = self.check_health()
                self.connected = bool(health.get("online"))
            except Exception:
                pass

    def get_endpoint_url(self, resource: str) -> str:
        """Returns the full URL for a resource using either custom or default route."""
        clean_base = (self.base_url or "").strip().rstrip("/")
        route = self.custom_routes.get(resource) or self.DEFAULT_ROUTES.get(resource, f"/api/v1/{resource}")
        if not route.startswith("/"):
            route = "/" + route
        return f"{clean_base}{route}"

    def _client(self) -> httpx.Client:
        """Returns an HTTP client configured with timeout and redirect following."""
        return httpx.Client(timeout=self.timeout, follow_redirects=True)

    def set_custom_routes(self, routes: Dict[str, str]):
        for k, v in routes.items():
            if v and str(v).strip():
                clean_route = str(v).strip()
                if not clean_route.startswith("/"):
                    clean_route = "/" + clean_route
                self.custom_routes[k] = clean_route

    def get_custom_routes(self) -> Dict[str, str]:
        return self.custom_routes

    def reset_custom_routes(self):
        self.custom_routes = dict(self.DEFAULT_ROUTES)




    def _get_headers(self) -> Dict[str, str]:
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if self.api_key and self.api_key.strip():
            clean_key = self.api_key.strip()
            raw_token = clean_key
            if "dental_crm_token=" in raw_token:
                parts = raw_token.split("dental_crm_token=")
                if len(parts) > 1:
                    raw_token = parts[1].split(";")[0].strip()

            headers["Authorization"] = f"Bearer {raw_token}"
            headers["x-api-key"] = raw_token
            headers["Cookie"] = f"dental_crm_token={raw_token}"
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

        # Save to CONFIG_FILE if connection succeeded so server reloads stay connected
        if self.connected:
            try:
                with open(CONFIG_FILE, "w") as f:
                    json.dump({
                        "crm_url": self.base_url,
                        "api_key": self.api_key,
                        "enabled": self.enabled,
                        "custom_routes": self.custom_routes
                    }, f, indent=2)
            except Exception:
                pass

        return {
            "success": self.connected,
            "connected": self.connected,
            "crm_url": self.base_url,
            "api_key_configured": bool(self.api_key),
            "diagnostics": health
        }

    def disconnect(self):
        """Purge active CRM credentials and remove persisted config file."""
        self.enabled = False
        self.connected = False
        self.base_url = ""
        self.api_key = ""
        self.set_schema_mapping(None)
        if CONFIG_FILE.exists():
            try:
                CONFIG_FILE.unlink()
            except Exception:
                pass

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
        url = self.get_endpoint_url("clinic")
        headers = self._get_headers()
        try:
            with self._client() as client:
                res = client.get(url, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    self.connected = True
                    return {
                        "online": True,
                        "status_code": 200,
                        "crm_url": self.base_url,
                        "clinic": data.get("clinic", {}),
                        "message": "Dental Clinic CRM is ONLINE and responding"
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
        avail_url = self.get_endpoint_url("availability")
        try:
            with self._client() as client:
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
        url = self.get_endpoint_url("clinic")
        headers = self._get_headers()

        try:
            with self._client() as client:
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

        url = self.get_endpoint_url("appointments")
        headers = self._get_headers()

        try:
            with self._client() as client:
                res = client.get(url, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    raw_apps = data.get("appointments", [])
                    normalized = []
                    
                    # Check if custom AI schema mapping is active
                    mapping = self.schema_mapping
                    for item in raw_apps:
                        if mapping:
                            def _lookup(field_key, default_val=""):
                                k = mapping.get(field_key, field_key)
                                if "." in k:
                                    curr = item
                                    for part in k.split("."):
                                        if isinstance(curr, dict) and part in curr:
                                            curr = curr[part]
                                        else:
                                            return default_val
                                    return curr or default_val
                                return item.get(k, default_val)

                            p_name = _lookup("patient_name") or item.get("patient_name") or item.get("name") or "Unknown Patient"
                            p_phone = _lookup("patient_phone") or item.get("patient_phone") or item.get("phone") or ""
                            p_date = _lookup("appointment_date") or item.get("appointment_date") or "Today"
                            p_time = _lookup("appointment_time") or item.get("appointment_time") or "10:00 AM"
                            p_treatment = _lookup("treatment_type") or item.get("treatment_name") or item.get("treatment_type") or "General Consultation"
                            p_doc = _lookup("doctor_name") or item.get("doctor_name") or "Dr. Alok Aggarwal"
                            p_notes = _lookup("notes") or item.get("notes") or ""
                            p_status = _lookup("status") or item.get("status") or "Confirmed"
                            sync_badge = "SYNCED (AI Mapped)"
                        else:
                            p_name = item.get("patient_name", "Unknown Patient")
                            p_phone = item.get("patient_phone", "")
                            p_date = item.get("appointment_date", "Today")
                            p_time = item.get("appointment_time", "10:00 AM")
                            p_treatment = item.get("treatment_name") or item.get("treatment_type", "General Consultation")
                            p_doc = item.get("doctor_name", "Dr. Alok Aggarwal")
                            p_notes = item.get("notes", "")
                            p_status = item.get("status", "Confirmed")
                            sync_badge = "SYNCED"

                        normalized.append({
                            "id": item.get("id"),
                            "clinic_id": item.get("clinic_id", "clinic_bangalore"),
                            "patient_name": p_name,
                            "patient_phone": p_phone,
                            "appointment_date": p_date,
                            "appointment_time": p_time,
                            "treatment_type": p_treatment,
                            "doctor_id": item.get("doctor_id"),
                            "doctor_name": p_doc,
                            "status": p_status,
                            "is_emergency": 1 if item.get("is_emergency") in (1, True, "1") else 0,
                            "booking_source": item.get("booked_by") or item.get("booking_source", "Dental CRM (PostgreSQL)"),
                            "notes": p_notes,
                            "created_at": item.get("created_at") or datetime.now().isoformat(),
                            "crm_appointment_id": item.get("id"),
                            "crm_synced": 1,
                            "crm_sync_status": sync_badge
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

        url = self.get_endpoint_url("appointments")
        headers = self._get_headers()
        payload = {"id": app_id, "status": new_status}
        try:
            with self._client() as client:
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

        url = self.get_endpoint_url("doctors")
        headers = self._get_headers()
        try:
            with self._client() as client:
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

        url = self.get_endpoint_url("doctors")
        headers = self._get_headers()
        payload = {"id": doctor_id, "is_available": 1 if is_available else 0}
        try:
            with self._client() as client:
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

        url = self.get_endpoint_url("services")
        headers = self._get_headers()
        try:
            with self._client() as client:
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

        url = self.get_endpoint_url("services")
        headers = self._get_headers()
        payload = {"id": service_id, "price_range": price_range, "base_price": min_price}
        try:
            with self._client() as client:
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

        url = self.get_endpoint_url("availability")
        headers = self._get_headers()

        params = {"date": self._normalize_date(date_str), "time_preference": time_preference}
        if doctor_id:
            params["doctor_id"] = doctor_id

        for attempt in range(2):
            try:
                with self._client() as client:
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

        url = self.get_endpoint_url("appointments")
        headers = self._get_headers()

        standard_dict = {
            "patient_name": patient_name,
            "patient_phone": patient_phone,
            "appointment_date": self._normalize_date(appointment_date),
            "appointment_time": appointment_time,
            "treatment_name": treatment_name,
            "treatment_type": treatment_name,
            "notes": notes,
            "booked_by": booked_by
        }
        if doctor_id:
            standard_dict["doctor_id"] = doctor_id

        # If custom AI schema mapping is active, apply outbound transform!
        if self.schema_mapping:
            payload = {}
            for std_key, val in standard_dict.items():
                target_key = self.schema_mapping.get(std_key, std_key)
                if "." in target_key:
                    parts = target_key.split(".")
                    cur = payload
                    for p in parts[:-1]:
                        if p not in cur:
                            cur[p] = {}
                        cur = cur[p]
                    cur[parts[-1]] = val
                else:
                    payload[target_key] = val
            # Ensure standard fallbacks if CRM requires them
            if "patient_name" not in payload and "patient_name" in standard_dict:
                payload["patient_name"] = patient_name
            if "patient_phone" not in payload and "patient_phone" in standard_dict:
                payload["patient_phone"] = patient_phone
        else:
            payload = standard_dict


        for attempt in range(2):
            try:
                with self._client() as client:
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
            "stats": self.last_stats,
            "has_ai_schema_mapping": bool(self.schema_mapping),
            "schema_mapping": self.schema_mapping,
            "custom_routes": self.custom_routes,
            "default_routes": self.DEFAULT_ROUTES,
            "has_custom_routes": bool(self.custom_routes != self.DEFAULT_ROUTES)
        }

    def set_schema_mapping(self, mapping: Optional[Dict[str, str]]):
        """Set dynamic schema mapping for universal CRM field translation."""
        self.schema_mapping = mapping

    def get_schema_mapping(self) -> Optional[Dict[str, str]]:
        return self.schema_mapping

# Singleton instance
crm_client = DentalCrmClient()

