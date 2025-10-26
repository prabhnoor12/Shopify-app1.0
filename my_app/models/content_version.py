"""
Database model for ContentVersion.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class ContentVersion(Base):
    __tablename__ = "content_versions"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    body_html = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason_for_change = Column(String(255))

    product = relationship("Product")
    updated_by = relationship("User")

    __table_args__ = {"comment": "Stores historical versions of product content"}
