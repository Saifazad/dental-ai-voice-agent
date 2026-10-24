import json
import httpx
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from app.services.dental_service import dental_service
from app.services.ai_schema_mapper import ai_schema_mapper
from app.integrations.crm_client import crm_client
from app.schemas.clinic import (
    CrmConnectRequest,
    AISchemaAnalyzeRequest,
    SaveMappingRequest,
    CustomRoutesRequest
)

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
    crm_client.disconnect()
    dental_service.clear_cache()
    return {
        "success": True,
        "connected": False,
        "message": "CRM disconnected successfully. All cached clinic data cleared."
    }

@router.post("/ai-auto-map")
def ai_auto_map_crm_schema(req: AISchemaAnalyzeRequest):
    """
    Tareeka 2 (AI Auto-Schema Matching):
    Takes arbitrary CRM sample JSON (or fetches live appointments from crm_url)
    and automatically matches all fields to standard voice agent schema with confidence scores.
    """
    sample_payload = None

    # Option A: Payload provided directly as JSON / dict / list
    if req.sample_json:
        if isinstance(req.sample_json, str):
            clean_str = req.sample_json.strip()
            try:
                sample_payload = json.loads(clean_str)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid JSON string provided: {str(e)}")
        else:
            sample_payload = req.sample_json

    # Option B: If no sample provided, attempt to fetch sample from crm_url / appointments endpoint
    if not sample_payload:
        target_url = req.crm_url or crm_client.get_crm_url()
        if target_url:
            clean_url = target_url.rstrip("/")
            candidate_endpoints = [
                f"{clean_url}/api/v1/appointments",
                f"{clean_url}/appointments",
                f"{clean_url}/api/appointments"
            ]
            for ep in candidate_endpoints:
                try:
                    with httpx.Client(timeout=3.0) as client:
                        resp = client.get(ep, headers=crm_client._get_headers())
                        if resp.status_code == 200:
                            data = resp.json()
                            if isinstance(data, dict):
                                sample_payload = data.get("appointments") or data.get("data") or data
                            else:
                                sample_payload = data
                            if sample_payload:
                                break
                except Exception:
                    continue

    if not sample_payload:
        raise HTTPException(
            status_code=400,
            detail="No sample JSON could be parsed or fetched from the CRM URL. Please paste a sample JSON record from your CRM."
        )

    analysis = ai_schema_mapper.analyze_schema(sample_payload)
    return analysis

@router.post("/save-mapping")
def save_crm_schema_mapping(req: SaveMappingRequest):
    """
    Saves and activates the AI-generated or user-approved schema mapping
    for dynamic bidirectional CRM sync.
    """
    cid = dental_service.resolve_clinic_id(req.clinic_id)
    ai_schema_mapper.set_active_mapping(cid, req.mapping)
    crm_client.set_schema_mapping(req.mapping)

    return {
        "success": True,
        "clinic_id": cid,
        "message": f"Successfully activated AI schema mapping with {len(req.mapping)} fields!",
        "active_mapping": req.mapping
    }

@router.get("/mapping")
def get_crm_schema_mapping(clinic_id: Optional[str] = Query(None)):
    """Returns active AI schema mapping for the clinic."""
    cid = dental_service.resolve_clinic_id(clinic_id)
    mapping = ai_schema_mapper.get_active_mapping(cid)
    return {
        "success": True,
        "clinic_id": cid,
        "is_custom": bool(crm_client.schema_mapping),
        "mapping": mapping
    }

@router.get("/custom-routes")
def get_custom_routes():
    """Returns currently configured CRM endpoint routes and standard defaults."""
    return {
        "success": True,
        "custom_routes": crm_client.get_custom_routes(),
        "default_routes": crm_client.DEFAULT_ROUTES,
        "has_custom_routes": bool(crm_client.custom_routes != crm_client.DEFAULT_ROUTES)
    }

@router.post("/custom-routes")
def set_custom_routes(req: CustomRoutesRequest):
    """
    Configures dynamic custom CRM endpoints (e.g. /get-doctors instead of /api/v1/doctors).
    Takes effect immediately without restarting or modifying backend code.
    """
    crm_client.set_custom_routes(req.routes)
    return {
        "success": True,
        "message": "Custom CRM endpoint routes activated successfully!",
        "custom_routes": crm_client.get_custom_routes(),
        "default_routes": crm_client.DEFAULT_ROUTES,
        "has_custom_routes": bool(crm_client.custom_routes != crm_client.DEFAULT_ROUTES)
    }

@router.post("/custom-routes/reset")
def reset_custom_routes():
    """Resets all endpoint routes to standard /api/v1/... defaults."""
    crm_client.reset_custom_routes()
    return {
        "success": True,
        "message": "All routes reset to standard defaults.",
        "custom_routes": crm_client.get_custom_routes(),
        "default_routes": crm_client.DEFAULT_ROUTES,
        "has_custom_routes": False
    }


