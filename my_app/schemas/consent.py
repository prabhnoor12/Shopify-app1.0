"""
Schemas for consent management in GDPR compliance.
"""

from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime


class ConsentPreferences(BaseModel):
    """User consent preferences"""
    necessary_cookies: bool = True
    analytics_cookies: bool = False
    marketing_cookies: bool = False
    functional_cookies: bool = False
    marketing_emails: bool = False
    product_updates: bool = False
    third_party_sharing: bool = False
    profiling: bool = False
    object_marketing: bool = False  # Right to object to marketing
    object_profiling: bool = False  # Right to object to profiling


class ConsentUpdateRequest(BaseModel):
    """Request to update consent preferences"""
    preferences: ConsentPreferences
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class ConsentWithdrawRequest(BaseModel):
    """Request to withdraw specific consent"""
    consent_type: str  # e.g., "marketing_cookies", "third_party_sharing"


class ObjectionRequest(BaseModel):
    """Request to object to data processing"""
    objection_type: str  # "marketing" or "profiling"
    reason: Optional[str] = None


class ConsentResponse(BaseModel):
    """Response containing consent information"""
    user_id: int
    preferences: ConsentPreferences
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    consent_version: str = "1.0"
