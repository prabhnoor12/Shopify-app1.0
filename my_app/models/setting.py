"""
Settings model for app or shop-specific settings.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from ..database import Base


class Setting(Base):
    __tablename__ = "setting"
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shopify_users.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    key = Column(String, nullable=False)
    value = Column(Text, nullable=True)
    value_type = Column(String, nullable=True)  # e.g., 'string', 'int', 'json', etc.
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
