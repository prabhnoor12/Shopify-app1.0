from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CouponBase(BaseModel):
    code: str
    inviter_user_id: int
    discount_type: str  # 'percentage' or 'flat'
    value: float = Field(..., gt=0)  # e.g., 50 for 50% or $50
    min_spend: Optional[float] = Field(None, ge=0)
    max_discount: Optional[float] = Field(None, ge=0)
    start_date: datetime
    end_date: datetime
    usage_limit: Optional[int] = Field(None, gt=0)
    per_user_limit: Optional[int] = Field(None, gt=0)
    used_count: int = Field(0, ge=0)


class Coupon(CouponBase):
    id: int
    created_at: datetime
    status: str  # Derived: 'active', 'expired', 'used_up', 'disabled'

    class Config:
        from_attributes = True


class CouponUpdate(BaseModel):
    discount_type: Optional[str] = None  # 'percentage' or 'flat'
    value: Optional[float] = Field(None, gt=0)  # e.g., 50 for 50% or $50
    min_spend: Optional[float] = Field(None, ge=0)
    max_discount: Optional[float] = Field(None, ge=0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    usage_limit: Optional[int] = Field(None, gt=0)
    per_user_limit: Optional[int] = Field(None, gt=0)
    status: Optional[str] = None  # 'active', 'disabled'


class CouponCreate(BaseModel):
    inviter_user_id: int
    discount_type: str  # 'percentage' or 'flat'
    value: float = Field(..., gt=0)
    min_spend: Optional[float] = Field(None, ge=0)
    max_discount: Optional[float] = Field(None, ge=0)
    expires_in_days: int = Field(30, gt=0)
    usage_limit: Optional[int] = Field(None, gt=0)
    per_user_limit: Optional[int] = Field(None, gt=0)


class Config:
    schema_extra = {
        "example": {
            "inviter_user_id": 1,
            "discount_type": "percentage",
            "value": 20.0,
            "min_spend": 100.0,
            "max_discount": 50.0,
            "expires_in_days": 30,
            "usage_limit": 100,
            "per_user_limit": 1,
        }
    }


class CouponRead(CouponBase):
    id: int
    created_at: datetime
    status: str  # Derived: 'active', 'expired', 'used_up', 'disabled'

    class Config:
        from_attributes = True


class CouponResponse(CouponBase):
    id: int
    created_at: datetime
    status: str  # Derived: 'active', 'expired', 'used_up', 'disabled'

    class Config:
        from_attributes = True
