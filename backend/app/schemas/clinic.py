from pydantic import BaseModel
from typing import Optional, Dict, Any, Union

class PriceUpdate(BaseModel):
    price_range: str
    min_price: int

class AvailabilityUpdate(BaseModel):
    is_available: bool

class CrmConnectRequest(BaseModel):
    crm_url: str = "http://localhost:3000"
    api_key: Optional[str] = ""
    clinic_id: Optional[str] = None

class AISchemaAnalyzeRequest(BaseModel):
    sample_json: Optional[Union[str, Dict[str, Any], list]] = None
    crm_url: Optional[str] = None
    clinic_id: Optional[str] = None

class SaveMappingRequest(BaseModel):
    clinic_id: Optional[str] = None
    mapping: Dict[str, str]

class CustomRoutesRequest(BaseModel):
    clinic_id: Optional[str] = None
    routes: Dict[str, str]


