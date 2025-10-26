"""
This module defines the Pydantic models for creating, reading, and updating
Variant records, ensuring data validation and consistency.
"""

from sqlalchemy import Column, Integer, ForeignKey, Text, Float, JSON, Boolean
from sqlalchemy.orm import relationship
from ..database import Base
from .segment_performance import SegmentPerformance


class Variant(Base):
    __tablename__ = "variants"

    id = Column(Integer, primary_key=True, index=True)
    ab_test_id = Column(Integer, ForeignKey("ab_tests.id"))
    experiment_id = Column(Integer, ForeignKey("experiments.id"))
    description = Column(Text, nullable=False)
    is_control = Column(Boolean, default=False)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0.0)
    traffic_allocation = Column(Float, default=100.0)
    continuous_metrics = Column(JSON, default=lambda: {})

    ab_test = relationship(
        "ABTest", back_populates="variants", foreign_keys=[ab_test_id]
    )
    experiment = relationship("Experiment", back_populates="variants")
    segment_performances = relationship(
        "SegmentPerformance", back_populates="variant", cascade="all, delete-orphan"
    )
