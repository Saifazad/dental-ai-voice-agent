"""
Pydantic schemas package for API validation.
"""
from app.schemas.appointment import AppointmentCreate, StatusUpdate
from app.schemas.clinic import (
    PriceUpdate, AvailabilityUpdate, CrmConnectRequest,
    AISchemaAnalyzeRequest, SaveMappingRequest, CustomRoutesRequest
)
from app.schemas.simulation import VoiceSimulationRequest
from app.schemas.vapi import (
    ToolFunction, ToolCall, VapiMessage, VapiWebhookPayload,
    ToolResultItem, VapiToolResponse
)

__all__ = [
    "AppointmentCreate",
    "StatusUpdate",
    "PriceUpdate",
    "AvailabilityUpdate",
    "CrmConnectRequest",
    "AISchemaAnalyzeRequest",
    "SaveMappingRequest",
    "CustomRoutesRequest",

    "VoiceSimulationRequest",
    "ToolFunction",
    "ToolCall",
    "VapiMessage",
    "VapiWebhookPayload",
    "ToolResultItem",
    "VapiToolResponse",
]

