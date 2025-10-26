from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime


class AuditLogBase(BaseModel):
    """
    Base schema for an audit log entry.
    Includes context fields for severity, tags, and source.
    All fields are type-annotated and documented for clarity.
    """

    user_id: Optional[int] = None  # User who performed the action
    shop_id: Optional[int] = None  # Shop context for the action
    action: str  # Description of the action
    details: Optional[Dict[str, Any]] = None  # JSON details of changes
    ip_address: Optional[str] = None  # IP address of the actor
    user_agent: Optional[str] = None  # User agent string
    event_type: Optional[str] = None  # Type of event (login, update, webhook, etc.)
    severity: Optional[str] = None  # Severity level (info, warning, critical)
    tags: Optional[str] = None  # Comma-separated tags for categorization
    source: Optional[str] = None  # Source of the event (api, web, system)


class AuditLogCreate(AuditLogBase):
    """
    Schema for creating a new audit log entry.
    Inherits all fields from AuditLogBase.
    """

    pass


class AuditLogRead(AuditLogBase):
    """
    Schema for reading an audit log entry from the database.
    Includes deleted_at for soft delete support.
    All fields are type-annotated and documented for clarity.
    """

    id: int  # Primary key
    created_at: datetime  # Timestamp of creation
    deleted_at: Optional[datetime] = None  # Timestamp of soft deletion
    model_config = ConfigDict(from_attributes=True)
