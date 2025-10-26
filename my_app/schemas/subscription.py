from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from ..models.subscription import SubscriptionStatus
from .plan import Plan


class SubscriptionBase(BaseModel):
    shop_id: int
    plan_id: int
    status: SubscriptionStatus = SubscriptionStatus.TRIALING
    trial_ends_at: Optional[datetime] = None
    current_billing_period_starts_at: Optional[datetime] = None
    current_billing_period_ends_at: Optional[datetime] = None


class SubscriptionCreate(SubscriptionBase):
    shopify_charge_id: Optional[int] = None
    confirmation_url: Optional[str] = None


class SubscriptionUpdate(BaseModel):
    plan_id: Optional[int] = None
    status: Optional[SubscriptionStatus] = None


class Subscription(SubscriptionBase):
    id: int
    plan: Plan
    shopify_charge_id: Optional[int] = None
    confirmation_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
