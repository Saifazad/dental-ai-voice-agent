import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend root
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BACKEND_DIR / ".env")

class Settings:
    PROJECT_NAME: str = "Dental AI Voice Agent"
    APP_SLUG: str = "dental-ai-voice-agent"
    VERSION: str = "2.0.0"
    PORT: int = int(os.getenv("PORT", 8000))

    # Base directories
    BASE_DIR: Path = BACKEND_DIR
    DATA_DIR: Path = BACKEND_DIR / "data"
    DB_PATH: Path = DATA_DIR / "dental_saas.db"

    # CRM Settings (Disconnected by default until a CRM is connected)
    DENTAL_CRM_BASE_URL: str = os.getenv("DENTAL_CRM_BASE_URL", "").rstrip("/")
    DENTAL_CRM_ENABLED: bool = os.getenv("DENTAL_CRM_ENABLED", "false").lower() in ("true", "1", "yes")
    DENTAL_CRM_API_KEY: str = os.getenv("DENTAL_CRM_API_KEY", "")
    try:
        DENTAL_CRM_TIMEOUT_SECONDS: float = float(os.getenv("DENTAL_CRM_TIMEOUT_SECONDS", "3.0"))
    except ValueError:
        DENTAL_CRM_TIMEOUT_SECONDS: float = 3.0

    # Vapi Webhook Secret
    VAPI_SECRET_HEADER: str = os.getenv("VAPI_SECRET_HEADER", "")

    # Google Sheets Settings
    GOOGLE_SHEET_ID: str = os.getenv("GOOGLE_SHEET_ID", "")
    CREDENTIALS_PATH: Path = BACKEND_DIR / "credentials" / "service_account.json"

settings = Settings()
