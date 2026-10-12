"""
Backward compatibility layer for dental_service module.
Re-exports from app.services.dental_service.
"""
from app.services.dental_service import dental_service, DentalService
from app.services.triage_service import EMERGENCY_KEYWORDS, evaluate_emergency

__all__ = ["dental_service", "DentalService", "EMERGENCY_KEYWORDS", "evaluate_emergency"]
