"""
This module defines the SegmentPerformance model.
"""

from sqlalchemy import Column, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from ..database import Base
from .segment import Segment


class SegmentPerformance(Base):
    __tablename__ = "segment_performances"

    id = Column(Integer, primary_key=True, index=True)
    variant_id = Column(Integer, ForeignKey("variants.id"), nullable=False)
    segment_id = Column(Integer, ForeignKey("segments.id"), nullable=False)
    impressions = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    revenue_data = Column(JSON, default=lambda: [])  # Storing list of revenue numbers

    variant = relationship("Variant", back_populates="segment_performances")
    segment = relationship("Segment", back_populates="performances")
