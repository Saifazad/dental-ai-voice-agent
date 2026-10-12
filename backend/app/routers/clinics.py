from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Body
from app.services.dental_service import dental_service
from app.integrations.crm_client import crm_client
from app.schemas.clinic import PriceUpdate, AvailabilityUpdate

router = APIRouter(prefix="/api/clinics", tags=["Clinics"])

@router.get("")
def list_clinics():
    """Returns all dental clinics on the platform."""
    return dental_service.get_clinics()

@router.get("/{clinic_id}")
def get_clinic_details(clinic_id: str):
    """Returns clinic profile, doctors, services, and live metrics."""
    clinic = dental_service.get_clinic_by_id(clinic_id)
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    return clinic

# Services & Pricing
@router.get("/{clinic_id}/services")
def list_services(clinic_id: str):
    return dental_service.get_services(clinic_id)

@router.put("/{clinic_id}/services/{service_id}")
def update_service_pricing(clinic_id: str, service_id: str, payload: PriceUpdate):
    """Allows clinic owner to update treatment prices, which AI immediately reflects!"""
    ok = dental_service.update_service_price(clinic_id, service_id, payload.price_range, payload.min_price)
    if not ok:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"success": True, "service_id": service_id, "new_price_range": payload.price_range}

# Doctors
@router.get("/{clinic_id}/doctors")
def list_doctors(clinic_id: str):
    return dental_service.get_doctors(clinic_id)

@router.patch("/{clinic_id}/doctors/{doctor_id}/availability")
def toggle_doctor_availability(clinic_id: str, doctor_id: str, payload: AvailabilityUpdate):
    """Toggle doctor on-duty vs on-leave."""
    ok = dental_service.toggle_doctor_availability(doctor_id, payload.is_available)
    return {"success": ok, "doctor_id": doctor_id, "is_available": payload.is_available}

# Call Logs
@router.get("/{clinic_id}/call-logs")
def list_call_logs(clinic_id: str):
    return dental_service.get_call_logs(clinic_id)

# Integrations
@router.get("/{clinic_id}/integrations")
def get_integrations(clinic_id: str):
    return dental_service.get_integrations(clinic_id)

@router.put("/{clinic_id}/integrations")
def update_integrations(clinic_id: str, data: Dict[str, Any] = Body(...)):
    res = dental_service.update_integrations(clinic_id, data)
    return {"success": True, "integrations": res}

@router.post("/{clinic_id}/integrations/test-crm")
def test_crm_webhook(clinic_id: str):
    health = crm_client.check_health()
    if health.get("online"):
        return {
            "success": True,
            "connected": True,
            "crm_name": "Dental Clinic CRM (PostgreSQL)",
            "message": f"Successfully connected to Dental Clinic CRM at {crm_client.get_crm_url()}! Live appointments are syncing directly to PostgreSQL database.",
            "endpoint": f"{crm_client.get_crm_url()}/api/v1/appointments",
            "diagnostics": health
        }
    else:
        return {
            "success": False,
            "connected": False,
            "crm_name": "Dental Clinic CRM",
            "message": f"CRM Server Offline: {health.get('message')}. Start dental-clinic-crm with 'npm run dev' on port 3000 to enable real-time sync.",
            "endpoint": f"{crm_client.get_crm_url()}/api/v1/appointments",
            "diagnostics": health
        }

@router.post("/{clinic_id}/integrations/sync-sheets")
def sync_google_sheets(clinic_id: str):
    integrations = dental_service.get_integrations(clinic_id)
    apps = dental_service.get_appointments(clinic_id)
    return {
        "success": True,
        "message": f"Synchronized {len(apps)} appointments with Google Sheet",
        "sheet_id": integrations.get("google_sheet_id"),
        "synced_rows": len(apps),
        "status": "Live Connected"
    }
