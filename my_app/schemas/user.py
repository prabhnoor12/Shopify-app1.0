from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    shop_domain: str
    is_active: bool = True
    plan: str = "free"
    generations_used: int = 0


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    plan: Optional[str] = None
    generations_used: Optional[int] = None
    last_login: Optional[datetime] = None
    last_ip: Optional[str] = None
    last_user_agent: Optional[str] = None


class UserRead(UserBase):
    id: int
    # ... existing code
    last_user_agent: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class User(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PasswordUpdate(BaseModel):
    new_password: str

class ProfileUpdate(BaseModel):
    email: str = None
    plan: str = None
