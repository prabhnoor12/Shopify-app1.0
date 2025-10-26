"""
User model for app administrators or general users, linked to a Shopify store.
"""

from typing import TYPE_CHECKING
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.sql import func
from ..database import Base

if TYPE_CHECKING:
    from .shop import ShopifyUser


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    owned_agencies = relationship("Agency", back_populates="owner")
    agencies = relationship("AgencyMember", back_populates="user")
    usage_events = relationship("UsageEvent", back_populates="user")
    teams_owned = relationship("Team", back_populates="owner")
    team_memberships = relationship("TeamMember", back_populates="user")
    usage = relationship("Usage", back_populates="user")

    # Type-hinted relationship for static analysis
    if TYPE_CHECKING:
        shopify_user: Mapped["ShopifyUser"]

    # Runtime relationship
    shopify_user = relationship(
        "ShopifyUser",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
