"""
API Routers package.
"""
from app.routers.clinics import router as clinics_router
from app.routers.appointments import router as appointments_router
from app.routers.crm import router as crm_router
from app.routers.simulation import router as simulation_router
from app.routers.webhooks import router as webhooks_router

__all__ = [
    "clinics_router",
    "appointments_router",
    "crm_router",
    "simulation_router",
    "webhooks_router",
]
