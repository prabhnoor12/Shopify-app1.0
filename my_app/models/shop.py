"""
Shopify User model, representing a Shopify store that has installed the app.
"""

from typing import TYPE_CHECKING, List
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.sql import func
from ..database import Base

if TYPE_CHECKING:
    from .user import User
    from .ab_test import ABTest
    from .brand_voice import BrandVoice
    from .usage_event import UsageEvent
    from .subscription import Subscription
    from .agency import AgencyClient


class ShopifyUser(Base):
    __tablename__ = "shopify_users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    shop_domain = Column(String, unique=True, index=True, nullable=False)
    access_token = Column(String, nullable=False)
    email = Column(String, nullable=True)
    country = Column(String, nullable=True)
    plan = Column(String, default="free")
    domain = Column(String, unique=True, index=True, nullable=False)
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    webhook_version = Column(String)
    generations_used = Column(Integer, default=0)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Type-hinted relationships for static analysis
    if TYPE_CHECKING:
        user: Mapped["User"]
        ab_tests: Mapped[List["ABTest"]]
        brand_voice: Mapped["BrandVoice"]
        usage_events: Mapped[List["UsageEvent"]]
        subscriptions: Mapped[List["Subscription"]]
        managing_agencies: Mapped[List["AgencyClient"]]
        consents: Mapped["Consent"]

    # Runtime relationships
    user = relationship("User", back_populates="shopify_user")
    ab_tests = relationship("ABTest", back_populates="shopify_user")
    brand_voice = relationship(
        "BrandVoice", back_populates="shopify_user", uselist=False
    )
    usage_events = relationship("UsageEvent", back_populates="shop")
    subscriptions = relationship("Subscription", back_populates="shopify_user")
    managing_agencies = relationship(
        "AgencyClient", back_populates="shop", cascade="all, delete-orphan"
    )
    consents = relationship("Consent", back_populates="user", uselist=False)
