from pydantic import BaseModel
from typing import Optional

class PriceUpdate(BaseModel):
    price_range: str
    min_price: int

class AvailabilityUpdate(BaseModel):
    is_available: bool

class CrmConnectRequest(BaseModel):
    crm_url: str = "http://localhost:3000"
    api_key: Optional[str] = ""
    clinic_id: Optional[str] = None
