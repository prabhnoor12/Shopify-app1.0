from sqlalchemy import Column, Integer, String, JSON, Numeric, CheckConstraint, Boolean
from sqlalchemy.orm import relationship
from ..database import Base


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    features = Column(JSON, nullable=False)  # e.g., {"descriptions": 50, "updates": 10}
    is_active = Column(Boolean, default=True)
    shopify_plan_name = Column(
        String, nullable=True
    )  # Corresponding Shopify plan name, if applicable

    subscriptions = relationship("Subscription", back_populates="plan")

    __table_args__ = (
        CheckConstraint("price >= 0", name="check_plan_price_non_negative"),
    )

    def __repr__(self):
        return f"<Plan(id={self.id}, name='{self.name}')>"
