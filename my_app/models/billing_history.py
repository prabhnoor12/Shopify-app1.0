from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Numeric,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class BillingHistory(Base):
    __tablename__ = "billing_history"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    amount_paid = Column(Numeric(10, 2), nullable=False)
    paid_at = Column(DateTime, default=datetime.utcnow)
    invoice_url = Column(String, nullable=True)

    subscription = relationship("Subscription", back_populates="billing_history")

    __table_args__ = (
        CheckConstraint(
            "amount_paid >= 0", name="check_billing_history_amount_paid_non_negative"
        ),
    )
