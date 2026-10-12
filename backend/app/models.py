"""
Backward compatibility layer for models module.
Re-exports from app.schemas.
"""
from app.schemas.vapi import (
    ToolFunction, ToolCall, VapiMessage, VapiWebhookPayload,
    ToolResultItem, VapiToolResponse
)

__all__ = [
    "ToolFunction", "ToolCall", "VapiMessage", "VapiWebhookPayload",
    "ToolResultItem", "VapiToolResponse"
]
