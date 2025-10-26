"""
This module defines the database model for scheduling A/B test rotations,
which are tasks that automatically determine a winner and adjust traffic.
"""

import enum
from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    ForeignKey,
    Text,
    JSON,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class ScheduledRotationStatus(str, enum.Enum):
    """Enum for the status of a scheduled A/B test rotation."""

    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScheduledABTestRotation(Base):
    __tablename__ = "scheduled_ab_test_rotations"

    id = Column(Integer, primary_key=True, index=True)
    ab_test_id = Column(Integer, ForeignKey("ab_tests.id"), nullable=False, index=True)
    status = Column(
        SQLEnum(ScheduledRotationStatus),
        default=ScheduledRotationStatus.PENDING,
        nullable=False,
    )
    scheduled_for = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="The time when the rotation is scheduled to run.",
    )
    executed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="The time when the rotation was actually executed.",
    )
    winner_variant_id = Column(
        Integer,
        ForeignKey("variants.id"),
        nullable=True,
        comment="The ID of the winning variant after execution.",
    )
    new_traffic_allocation = Column(
        JSON,
        nullable=True,
        comment="The new traffic allocation percentages after rotation.",
    )
    execution_log = Column(
        Text, nullable=True, comment="Logs or error messages from the execution."
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    ab_test = relationship("ABTest", back_populates="scheduled_rotations")
    winner_variant = relationship("Variant")

    def __repr__(self):
        return f"<ScheduledABTestRotation(id={self.id}, ab_test_id={self.ab_test_id}, status='{self.status}')>"
