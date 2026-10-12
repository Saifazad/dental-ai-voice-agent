import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from app.core.config import settings

class AppointmentSheetsService:
    def __init__(self):
        self.use_google_sheets = False
        self.sheet = None
        self._init_google_sheets()

    def _init_google_sheets(self):
        spreadsheet_id = settings.GOOGLE_SHEET_ID
        creds_path = settings.CREDENTIALS_PATH
        if creds_path.exists() and spreadsheet_id:
            try:
                import gspread
                from google.oauth2.service_account import Credentials
                scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
                creds = Credentials.from_service_account_file(str(creds_path), scopes=scopes)
                client = gspread.authorize(creds)
                self.sheet = client.open_by_key(spreadsheet_id).sheet1
                self.use_google_sheets = True
                print(" Successfully connected to Google Sheets!")
            except Exception as e:
                print(f"⚠️ Google Sheets connection failed: {e}. Falling back to local data/appointments.json")
                self.use_google_sheets = False
        else:
            print("ℹ️ Running in Demo Mode (Local Storage). Add credentials/service_account.json and GOOGLE_SHEET_ID in .env to enable live Google Sheets sync.")

    def book_appointment(self, patient_name: str, patient_phone: str, appointment_date: str, appointment_time: str, treatment_type: str = "Consultation", notes: str = "") -> Dict[str, Any]:
        """Book an appointment in Google Sheets or local fallback."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = {
            "timestamp": timestamp,
            "patient_name": patient_name,
            "patient_phone": patient_phone,
            "appointment_date": appointment_date,
            "appointment_time": appointment_time,
            "treatment_type": treatment_type,
            "status": "Confirmed (AI Receptionist)",
            "notes": notes
        }

        if self.use_google_sheets and self.sheet:
            try:
                row = [timestamp, patient_name, patient_phone, appointment_date, appointment_time, treatment_type, "Confirmed (AI)", notes]
                self.sheet.append_row(row)
                return {"success": True, "source": "Google Sheets", "data": record}
            except Exception as e:
                print(f"Error appending to Google Sheet: {e}. Saving locally instead.")

        return self._save_to_local_file(record)

    def _save_to_local_file(self, record: Dict[str, Any]) -> Dict[str, Any]:
        data_file = settings.DATA_DIR / "appointments.json"
        os.makedirs(settings.DATA_DIR, exist_ok=True)
        appointments = []
        if data_file.exists():
            try:
                with open(data_file, "r", encoding="utf-8") as f:
                    appointments = json.load(f)
            except Exception:
                appointments = []

        appointments.append(record)
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(appointments, f, indent=2, ensure_ascii=False)

        return {"success": True, "source": "Local JSON", "data": record}

# Singleton instance
appointment_sheets_service = AppointmentSheetsService()
