import enum
from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    ForeignKey,
    Enum,
    CheckConstraint,
    String,
    Float,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base
from .billing_history import BillingHistory  # noqa: F401
from .plan import Plan  # noqa: F401


class SubscriptionStatus(enum.Enum):
    TRIALING = "trialing"
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    PENDING = "pending"  # New status for pending plan changes


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("shopify_users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    shopify_charge_id = Column(
        Integer, nullable=True
    )  # Store Shopify's recurring application charge ID
    confirmation_url = Column(
        String, nullable=True
    )  # URL for user to accept the charge
    status = Column(
        Enum(SubscriptionStatus),
        index=True,
        nullable=False,
        default=SubscriptionStatus.TRIALING,
    )
    trial_ends_at = Column(DateTime, nullable=True)
    current_billing_period_starts_at = Column(DateTime, nullable=True)
    current_billing_period_ends_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    price = Column(Float, nullable=False)

    shopify_user = relationship("ShopifyUser", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
    billing_history = relationship("BillingHistory", back_populates="subscription")

    __table_args__ = (
        CheckConstraint(
            "current_billing_period_ends_at >= current_billing_period_starts_at",
            name="check_billing_period_dates",
        ),
    )

    def __repr__(self):
        return f"<Subscription(id={self.id}, status='{self.status}')>"
