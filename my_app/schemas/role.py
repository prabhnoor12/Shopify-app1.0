from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from .permission import Permission


# --- Role Schemas ---
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    permission_ids: List[int] = []
    parent_role_id: Optional[int] = None


class RoleUpdate(RoleBase):
    permission_ids: List[int] = []
    parent_role_id: Optional[int] = None


class Role(RoleBase):
    id: int
    permissions: List[Permission] = []
    parent_role_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
