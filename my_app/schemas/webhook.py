from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime


class WebhookEventBase(BaseModel):
    """Base schema for webhook events."""

    event_type: str
    payload: Dict[str, Any]


class WebhookEventCreate(WebhookEventBase):
    """Schema for creating a new webhook event record."""

    pass


class WebhookEventUpdate(BaseModel):
    """Schema for updating a webhook event."""

    status: Optional[str] = None
    processed_at: Optional[datetime] = None
    error: Optional[str] = None


class WebhookEventRead(WebhookEventBase):
    """Schema for reading a webhook event, including processing status."""

    id: int
    status: str
    received_at: datetime
    processed_at: Optional[datetime] = None
    error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
