from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CouponUsageLog(BaseModel):
    id: int
    coupon_id: int
    user_id: int
    order_id: Optional[int] = None
    used_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CouponUsageLogCreate(BaseModel):
    coupon_id: int
    user_id: int
    order_id: Optional[int] = None
    used_at: datetime


model_config = ConfigDict(from_attributes=True)


class CouponUsageLogRead(BaseModel):
    id: int
    coupon_id: int
    user_id: int
    order_id: Optional[int] = None
    used_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CouponUsageLogBase(BaseModel):
    coupon_id: int
    user_id: int
    order_id: Optional[int] = None


class CouponUsageLogResponse(CouponUsageLogBase):
    id: int
    used_at: datetime

    model_config = ConfigDict(from_attributes=True)
