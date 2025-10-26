from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    Enum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import (
    JSON,
)  # Assuming PostgreSQL for JSONB, otherwise use Text
from ..database import Base
import enum


class ScheduledTaskStatus(str, enum.Enum):
    PENDING = "pending"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False
    )  # Assuming user_id links to the merchant
    task_type = Column(
        String, nullable=False
    )  # e.g., "product_description_update", "ab_test_rotation", "discount_activation"
    scheduled_time = Column(DateTime(timezone=True), nullable=False)
    payload = Column(JSON, nullable=False)  # Use JSONB for PostgreSQL, otherwise Text
    status = Column(
        Enum(ScheduledTaskStatus), default=ScheduledTaskStatus.PENDING, nullable=False
    )
    executed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # Fields for recurring tasks
    recurrence_rule = Column(String, nullable=True)  # For storing RRULE strings
    parent_task_id = Column(Integer, ForeignKey("scheduled_tasks.id"), nullable=True)

    user = relationship("User")


class TaskExecutionLog(Base):
    __tablename__ = "task_execution_logs"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("scheduled_tasks.id"), nullable=False)
    status = Column(String, nullable=False)
    log = Column(Text, nullable=True)
    executed_at = Column(DateTime(timezone=True), default=func.now())


class TaskExecutionLogCreate:
    def _init__(self, task_id: int, status: str, log: str = None):
        self.task_id = task_id
        self.status = status
        self.log = log


class ScheduledUpdate(Base):
    __tablename__ = "scheduled_updates"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    update_type = Column(
        String, nullable=False
    )  # e.g., "product_description", "ab_test", "discount"
    target_id = Column(
        Integer, nullable=False
    )  # ID of the product, AB test, or discount
    new_value = Column(
        Text, nullable=False
    )  # New description text, AB test config, or discount details
    scheduled_time = Column(DateTime(timezone=True), nullable=False)
    is_executed = Column(Boolean, default=False)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ScheduledUpdateCreate:
    def __init__(
        self,
        user_id: int,
        update_type: str,
        target_id: int,
        new_value: str,
        scheduled_time: DateTime,
    ):
        self.user_id = user_id
        self.update_type = update_type
        self.target_id = target_id
        self.new_value = new_value
        self.scheduled_time = scheduled_time


class ScheduledUpdateRead:
    def __init__(
        self,
        id: int,
        user_id: int,
        update_type: str,
        target_id: int,
        new_value: str,
        scheduled_time: DateTime,
        is_executed: bool,
        executed_at: DateTime,
        created_at: DateTime,
        updated_at: DateTime,
    ):
        self.id = id
        self.user_id = user_id
        self.update_type = update_type
        self.target_id = target_id
        self.new_value = new_value
        self.scheduled_time = scheduled_time
        self.is_executed = is_executed
        self.executed_at = executed_at
        self.created_at = created_at
        self.updated_at = updated_at
