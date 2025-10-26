from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from ..database import Base


class Coupon(Base):
    __tablename__ = "coupons"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    inviter_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    discount_type = Column(String, nullable=False)  # 'percentage' or 'flat'
    value = Column(Float, nullable=False)  # e.g., 50 for 50% or $50
    min_spend = Column(Float, nullable=True)
    max_discount = Column(Float, nullable=True)
    start_date = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    end_date = Column(DateTime(timezone=True), nullable=False)
    usage_limit = Column(Integer, nullable=True)  # Total uses allowed
    per_user_limit = Column(Integer, nullable=True)
    used_count = Column(Integer, default=0, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
