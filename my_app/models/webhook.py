"""
Webhook model for logging or tracking webhook events.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from ..database import Base


class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    id = Column(Integer, primary_key=True, index=True)
    shop_id = Column(Integer, ForeignKey("shopify_users.id"), nullable=False)
    event_id = Column(
        String, index=True, nullable=True
    )  # Shopify webhook idempotency key
    topic = Column(String, nullable=False)
    payload = Column(Text, nullable=False)
    status = Column(
        String, default="received"
    )  # e.g., 'received', 'processed', 'error'
    processed_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(Text, nullable=True)
    received_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
