from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
from .user import User
from datetime import datetime
from ..models.team import TeamMemberStatus
from .role import Role


# --- Team Member Schemas ---
class TeamMemberBase(BaseModel):
    user_id: int
    team_id: int
    role_id: int


class TeamMemberCreate(BaseModel):
    user_id: int
    role_id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class TeamMemberUpdate(BaseModel):
    role_id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class TeamMember(TeamMemberBase):
    id: int
    status: TeamMemberStatus
    user: User
    role: Role
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Team Schemas ---
class TeamBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = Field(None, max_length=255)


class TeamCreate(TeamBase):
    pass


class TeamUpdate(TeamBase):
    name: Optional[str] = Field(None, min_length=3, max_length=50)
    description: Optional[str] = Field(None, max_length=255)


class Team(TeamBase):
    id: int
    owner_id: int
    owner: User
    members: List[TeamMember] = []
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Invitation Schemas ---
class InvitationCreate(BaseModel):
    email: EmailStr
    role_id: int


class Invitation(BaseModel):
    id: int
    email: EmailStr
    team_id: int
    role_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Ownership Transfer Schemas ---
class TransferOwnershipRequest(BaseModel):
    new_owner_id: int
