from pydantic import BaseModel, ConfigDict
from typing import Optional, Any
from datetime import datetime


class SettingBase(BaseModel):
    """Base schema for settings, defining the core fields."""

    shop_id: int
    key: str
    value: Any


class SettingCreate(SettingBase):
    """Schema for creating a new setting."""

    pass


class SettingUpdate(BaseModel):
    """Schema for updating an existing setting. Only the value can be updated."""

    value: Optional[Any] = None


class SettingRead(SettingBase):
    """Schema for reading a setting, including database-generated fields."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class Setting(SettingBase):
    """Schema for reading a setting, including database-generated fields."""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
