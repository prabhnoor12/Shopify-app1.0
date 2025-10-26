from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from .permission import Permission
from datetime import datetime


class CustomRoleBase(BaseModel):
    name: str
    description: Optional[str] = None


class CustomRoleCreate(CustomRoleBase):
    permission_ids: List[int] = []
    parent_role_id: Optional[int] = None


class CustomRoleUpdate(CustomRoleBase):
    permission_ids: List[int] = []
    parent_role_id: Optional[int] = None


class CustomRole(CustomRoleBase):
    id: int
    team_id: int
    permissions: List[Permission] = []
    parent_role_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
