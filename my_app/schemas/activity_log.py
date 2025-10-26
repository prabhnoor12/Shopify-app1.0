from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from .user import User


class ActivityLogBase(BaseModel):
    action: str
    details: Optional[Dict[str, Any]] = None


class ActivityLogCreate(ActivityLogBase):
    team_id: int
    user_id: int


class ActivityLog(ActivityLogBase):
    id: int
    team_id: int
    user: User
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
