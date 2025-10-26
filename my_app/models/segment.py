"""
This module defines the Segment model.
"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from ..database import Base


class Segment(Base):
    __tablename__ = "segments"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(
        String, nullable=False, index=True
    )  # e.g., 'location', 'referral_source'
    value = Column(String, nullable=False, index=True)  # e.g., 'US', 'techblog.com'

    performances = relationship(
        "SegmentPerformance", back_populates="segment", cascade="all, delete-orphan"
    )
