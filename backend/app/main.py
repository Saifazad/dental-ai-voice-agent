import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import (
    clinics_router,
    appointments_router,
    crm_router,
    simulation_router,
    webhooks_router,
    mock_crm_router
)
from app.schemas import (
    AppointmentCreate,
    StatusUpdate,
    PriceUpdate,
    AvailabilityUpdate,
    VoiceSimulationRequest,
    CrmConnectRequest
)

# FastAPI Application Instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Stateless Headless B2B Voice Gateway for Dental Clinic CRMs",
    version=settings.VERSION
)

# 3. Global Middleware (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Include Feature Routers
app.include_router(clinics_router)
app.include_router(appointments_router)
app.include_router(crm_router)
app.include_router(simulation_router)
app.include_router(webhooks_router)
app.include_router(mock_crm_router)

# 5. Root & Health Check Endpoint
@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "mode": "Stateless Headless CRM Gateway",
        "database": "None (100% Direct CRM Proxy)"
    }

# 6. Local Development Server Runner
if __name__ == "__main__":
    port = settings.PORT
    print(f"🚀 Starting {settings.PROJECT_NAME} v{settings.VERSION} on port {port}...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
