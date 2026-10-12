"""
Backward compatibility layer for sheets_service.
Re-exports from app.integrations.sheets_service.
"""
from app.integrations.sheets_service import appointment_sheets_service as appointment_service, AppointmentSheetsService

__all__ = ["appointment_service", "AppointmentSheetsService"]
