from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ToolFunction(BaseModel):
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)

class ToolCall(BaseModel):
    id: str
    type: Optional[str] = "function"
    function: ToolFunction

class VapiMessage(BaseModel):
    type: str
    toolCalls: Optional[List[ToolCall]] = None
    call: Optional[Dict[str, Any]] = None
    transcript: Optional[str] = None
    summary: Optional[str] = None
    recordingUrl: Optional[str] = None

class VapiWebhookPayload(BaseModel):
    message: VapiMessage

class ToolResultItem(BaseModel):
    toolCallId: str
    result: Any

class VapiToolResponse(BaseModel):
    results: List[ToolResultItem]
