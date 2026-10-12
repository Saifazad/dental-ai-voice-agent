from typing import Optional
from fastapi import APIRouter, Query
from app.services.dental_service import dental_service
from app.integrations.crm_client import crm_client
from app.schemas.clinic import CrmConnectRequest

router = APIRouter(prefix="/api/crm", tags=["Dental CRM Integration"])

@router.post("/connect")
def connect_crm(req: CrmConnectRequest):
    """
    Connect to Dental CRM via Base URL & optional API Key.
    Performs handshake, tests authentication, and immediately fetches live appointments,
    doctors, and services to load into the dashboard.
    """
    config_res = crm_client.configure(req.crm_url, req.api_key, enabled=True)

    if not config_res.get("connected"):
        return {
            "success": False,
            "connected": False,
            "message": config_res.get("diagnostics", {}).get("message", "Cannot connect to CRM server. Make sure it is running on the specified URL."),
            "crm_url": req.crm_url,
            "diagnostics": config_res.get("diagnostics")
        }

    crm_clinic = crm_client.get_crm_clinic()
    cid = crm_clinic.get("id") if crm_clinic else dental_service.resolve_clinic_id(req.clinic_id)

    # Persist config in database
    dental_service.update_integrations(cid, {
        "crm_base_url": req.crm_url,
        "crm_api_key": req.api_key or "",
        "crm_enabled": True,
        "crm_type": "Dental Clinic CRM"
    })

    # Fetch live data immediately
    sync_result = dental_service.sync_all_from_crm(cid)
    return sync_result

@router.post("/sync")
def sync_crm(clinic_id: Optional[str] = Query(None)):
    """Force pull fresh appointments, doctors, and treatments from Dental Clinic CRM."""
    cid = dental_service.resolve_clinic_id(clinic_id)
    return dental_service.sync_all_from_crm(cid)

@router.get("/status")
def get_crm_status(clinic_id: Optional[str] = Query(None)):
    """Returns live connection status & stats with Dental CRM."""
    return {
        "success": True,
        **crm_client.get_sync_status()
    }

@router.post("/disconnect")
def disconnect_crm(clinic_id: Optional[str] = Query(None)):
    """Disconnects CRM and clears cached data."""
    crm_client.enabled = False
    crm_client.connected = False
    crm_client.base_url = ""
    crm_client.api_key = ""
    dental_service.clear_cache()
    return {
        "success": True,
        "connected": False,
        "message": "CRM disconnected successfully. All cached clinic data cleared."
    }
