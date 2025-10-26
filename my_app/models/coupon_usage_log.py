from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from ..database import Base


class CouponUsageLog(Base):
    __tablename__ = "coupon_usage_logs"
    id = Column(Integer, primary_key=True, index=True)
    coupon_id = Column(Integer, ForeignKey("coupons.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_id = Column(
        Integer, nullable=True
    )  # Optional: Link to an order if applicable
    used_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
