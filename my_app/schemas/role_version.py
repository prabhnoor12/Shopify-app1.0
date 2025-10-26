from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from .user import User


class RoleVersionBase(BaseModel):
    version: int
    name: str
    description: Optional[str] = None
    permissions: Optional[List[Dict[str, Any]]] = None


class RoleVersionRead(RoleVersionBase):
    id: int
    role_id: int
    updated_by_id: int
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RoleVersionCreate(RoleVersionBase):
    role_id: int
    updated_by_id: int


class RoleVersion(RoleVersionBase):
    id: int
    role_id: int
    updated_by: User
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_role_id: Optional[int] = None
    permission_ids: List[int] = []


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_role_id: Optional[int] = None
    permission_ids: Optional[List[int]] = None
