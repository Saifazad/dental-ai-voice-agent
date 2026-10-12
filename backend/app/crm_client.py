"""
Backward compatibility layer for crm_client.
Re-exports from app.integrations.crm_client.
"""
from app.integrations.crm_client import crm_client, DentalCrmClient

__all__ = ["crm_client", "DentalCrmClient"]
