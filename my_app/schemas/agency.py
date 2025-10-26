"""
This module defines the Pydantic schemas for the Agency feature, which are
used for API validation, serialization, and documentation.
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from ..models.agency import AgencyRole

# --- Agency Schemas ---


class AgencyBase(BaseModel):
    name: str


class AgencyCreate(AgencyBase):
    pass


class AgencyUpdate(AgencyBase):
    name: Optional[str] = None


class Agency(AgencyBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Agency Member Schemas ---


class AgencyMemberBase(BaseModel):
    user_id: int
    role: AgencyRole = AgencyRole.MEMBER


class AgencyMemberCreate(AgencyMemberBase):
    pass

class AgencyMemberUpdate(AgencyMemberBase):
    pass

class AgencyMember(AgencyMemberBase):
    agency_id: int

    class Config:
        from_attributes = True


# --- Agency Client Schemas ---


class AgencyClientBase(BaseModel):
    shop_id: int


class AgencyClientCreate(AgencyClientBase):
    pass


class AgencyClient(AgencyClientBase):
    agency_id: int

    class Config:
        from_attributes = True


# --- Schemas with Relationships for Detailed Views ---


class AgencyMemberWithDetails(AgencyMember):
    # Add user details if needed, e.g., from a User schema
    pass


class AgencyClientWithDetails(AgencyClient):
    # Add shop details if needed, e.g., from a Shop schema
    pass


class AgencyDetails(Agency):
    members: List[AgencyMemberWithDetails] = []
    clients: List[AgencyClientWithDetails] = []
