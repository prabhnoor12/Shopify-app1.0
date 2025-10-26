from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from ..database import Base


class BillingRecord(Base):
    __tablename__ = "billing_records"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, paid, failed
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    paid_at = Column(DateTime(timezone=True), nullable=True)
