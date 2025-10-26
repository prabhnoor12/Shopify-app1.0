from typing import Optional
from pydantic import BaseModel, ConfigDict


class PermissionBase(BaseModel):
    resource: str
    action: str
    scope: Optional[str] = None


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(PermissionBase):
    pass


class Permission(PermissionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
