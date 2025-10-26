from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class GDPRDataRequest(BaseModel):
    """Request for data access or deletion"""
    email: EmailStr
    request_type: str  # "access" or "delete"
    reason: Optional[str] = None
    format: Optional[str] = "json"  # "json", "csv", or "xml"


class GDPRDataResponse(BaseModel):
    """Response containing user data for access requests"""
    user_data: dict
    audit_logs: list
    sessions: list
    usage_data: dict
    export_date: datetime


class GDPRRequestStatus(BaseModel):
    """Status of a GDPR request"""
    request_id: str
    status: str  # "pending", "processing", "completed", "rejected"
    request_type: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    download_url: Optional[str] = None


class DataRectificationRequest(BaseModel):
    """Request to rectify/update personal data"""
    email: EmailStr
    field: str  # Field to update: "email", "shop_domain", etc.
    new_value: str
    reason: Optional[str] = None
