from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from ..database import Base


class GenericWebhookEvent(Base):
    __tablename__ = "generic_webhook_events"
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False)
    payload = Column(Text, nullable=False)
    status = Column(String, default="received")
    received_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    processed_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(Text, nullable=True)
