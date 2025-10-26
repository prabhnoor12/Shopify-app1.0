"""
This module defines the Pydantic models for creating, reading, and updating
A/B Test records, ensuring data validation and consistency.
"""

from enum import Enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Boolean,
    Enum as SQLAlchemyEnum,
)
from sqlalchemy.orm import relationship, Mapped
from typing import TYPE_CHECKING

from ..database import Base

if TYPE_CHECKING:
    from .shop import ShopifyUser


class ABTestStatus(Enum):
    DRAFT = "DRAFT"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"
    CONCLUDED = "CONCLUDED"


class ABTest(Base):
    __tablename__ = "ab_tests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("shopify_users.id"), nullable=False)
    shopify_user = relationship("ShopifyUser", back_populates="ab_tests")
    product_id = Column(String, nullable=False)  # Product ID is an integer
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    test_type = Column(String, nullable=False)
    status = Column(SQLAlchemyEnum(ABTestStatus), default=ABTestStatus.DRAFT)
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    end_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Use a string for variant IDs to avoid circular dependency issues with ForeignKey
    active_variant_id = Column(Integer, nullable=True)
    winner_variant_id = Column(Integer, nullable=True)

    auto_optimize = Column(Boolean, default=False)
    auto_optimize_cooldown_days = Column(Integer, default=7)
    goal_metric = Column(String, default="conversion_rate")

    variants = relationship(
        "Variant", back_populates="ab_test", cascade="all, delete-orphan"
    )
    shopify_user: Mapped["ShopifyUser"] = relationship(
        "ShopifyUser", back_populates="ab_tests"
    )
    scheduled_rotations = relationship(
        "ScheduledABTestRotation", back_populates="ab_test"
    )
