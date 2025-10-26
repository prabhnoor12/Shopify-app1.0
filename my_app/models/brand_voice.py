"""
This module defines the Pydantic models for creating, reading, and updating
Brand Voice records, ensuring data validation and consistency.
"""

from typing import TYPE_CHECKING
from sqlalchemy import Column, Integer, String, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

if TYPE_CHECKING:
    from .shop import ShopifyUser

from ..database import Base


class BrandVoice(Base):
    __tablename__ = "brand_voice"

    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(
        Integer, ForeignKey("shopify_users.id"), unique=True, nullable=False
    )
    tone_of_voice = Column(
        String, nullable=True
    )  # e.g., formal, playful, authoritative
    vocabulary_preferences = Column(
        JSON, nullable=True
    )  # e.g., {"preferred": ["clients"], "avoid": ["customers"]}
    industry_jargon = Column(JSON, nullable=True)  # e.g., ["synergy", "paradigm shift"]
    banned_words = Column(JSON, nullable=True)  # e.g., ["awesome", "literally"]
    description = Column(
        Text, nullable=True
    )  # Keep for backward compatibility or general notes

    shopify_user = relationship("ShopifyUser", back_populates="brand_voice")
