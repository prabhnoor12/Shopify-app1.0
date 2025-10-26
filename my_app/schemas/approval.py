"""
This module defines the Pydantic schemas for the content approval workflow,
which are used for API validation, serialization, and documentation.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from ..models.approval import ApprovalStatus

# --- Approval Request Schemas ---


class ApprovalRequestBase(BaseModel):
    product_id: int
    content_to_approve: str
    expires_at: Optional[datetime] = None


class ApprovalRequestCreate(ApprovalRequestBase):
    pass


class ApprovalRequest(ApprovalRequestBase):
    id: int
    token: str
    agency_id: int
    requester_id: int
    status: ApprovalStatus
    client_comment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Approval Response Schema (for the client) ---


class ApprovalResponse(BaseModel):
    status: ApprovalStatus
    comment: Optional[str] = None
