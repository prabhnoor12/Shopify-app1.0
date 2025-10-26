"""
Product model for storing product metadata or sync info.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Float,
    Text,
    Boolean,
    Enum,
)
from sqlalchemy.sql import func
from ..database import Base
from ..schemas.enums import ProductStatus


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shopify_users.id"), nullable=False)
    shopify_product_id = Column(String, index=True, nullable=False)
    title = Column(String, nullable=False)
    body_html = Column(Text, nullable=True)
    product_type = Column(String, nullable=True)
    tags = Column(String, nullable=True)
    vendor = Column(String, nullable=True)
    status = Column(
        Enum(ProductStatus),
        nullable=False,
        default=ProductStatus.SYNCED,
        server_default=ProductStatus.SYNCED.value,
    )
    price = Column(Float, nullable=True)
    is_published = Column(Boolean, default=True)
    audit_findings = Column(Text, nullable=True)  # To store audit results
    performance_category = Column(String, nullable=True)  # e.g., "Winner", "Dud", "Hidden Gem"
    ai_performance_summary = Column(Text, nullable=True)  # To store AI-generated insights
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    category = Column(String, index=True)
