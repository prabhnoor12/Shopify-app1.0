from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from ..database import Base
from datetime import datetime


class UsageEvent(Base):
    __tablename__ = "usage_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    shop_id = Column(Integer, ForeignKey("shopify_users.id"), nullable=False)
    feature_name = Column(String, index=True, nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    context = Column(JSON, nullable=True)  # Flexible JSON field for additional context
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="usage_events")
    shop = relationship("ShopifyUser", back_populates="usage_events")
