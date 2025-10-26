"""
Pydantic schema for Session model.
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class SessionBase(BaseModel):
    user_id: Optional[int] = None
    shop_id: Optional[int] = None
    session_token: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device: Optional[str] = None
    is_active: Optional[bool] = True
    expires_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None


class SessionCreate(SessionBase):
    pass


class SessionUpdate(BaseModel):
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None


class SessionRead(SessionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class Session(SessionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
