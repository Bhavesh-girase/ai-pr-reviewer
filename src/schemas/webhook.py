from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field

class WebhookRequest(BaseModel):
    payload: Dict[str, Any]

class WebhookStatusResponseSchema(BaseModel):
    project_id: str
    webhook_status: str  # NOT_REGISTERED, REGISTERING, ACTIVE, FAILED, DISABLED
    webhook_registered_at: Optional[datetime] = None
    last_webhook_event_at: Optional[datetime] = None
    github_webhook_id: Optional[int] = None
    webhook_url: Optional[str] = None

class WebhookRegisterResponseSchema(BaseModel):
    message: str
    github_webhook_id: Optional[int] = None
    webhook_status: str
    synced_prs_count: int = 0

class WebhookDeliverySchema(BaseModel):
    id: str
    project_id: Optional[str] = None
    delivery_id: str
    event_type: str
    action: Optional[str] = None
    received_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    status: str
    error_message: Optional[str] = None