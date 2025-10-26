from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SQLEnum
from ..database import Base
import enum


class ExperimentStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"


class ExperimentType(str, enum.Enum):
    AB_TEST = "AB_TEST"
    MAB_TEST = "MAB_TEST"


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(
        SQLEnum(ExperimentType), default=ExperimentType.AB_TEST, nullable=False
    )
    status = Column(
        SQLEnum(ExperimentStatus), default=ExperimentStatus.DRAFT, nullable=False
    )
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    variants = relationship("Variant", back_populates="experiment")


class UserVariantAssignment(Base):
    __tablename__ = "user_variant_assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("shopify_users.id"), nullable=False)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("variants.id"), nullable=False)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("ShopifyUser")
    experiment = relationship("Experiment")
    variant = relationship("Variant")

    __table_args__ = (
        UniqueConstraint("user_id", "experiment_id", name="_user_experiment_uc"),
    )
