"""
External integrations package (CRM, Google Sheets, etc.).
"""
from app.integrations.crm_client import crm_client, DentalCrmClient
from app.integrations.sheets_service import appointment_sheets_service, AppointmentSheetsService

__all__ = ["crm_client", "DentalCrmClient", "appointment_sheets_service", "AppointmentSheetsService"]
