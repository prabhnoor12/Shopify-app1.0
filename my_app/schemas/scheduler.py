from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..models.scheduler import ScheduledTaskStatus


# Basic User schema for nesting
class User(BaseModel):
    id: int
    email: str

    # Add other user fields if needed, like name
    class Config:
        from_attributes = True


# Task Execution Log Schemas
class TaskExecutionLogBase(BaseModel):
    status: ScheduledTaskStatus
    log_message: Optional[str] = None


class TaskExecutionLogCreate(TaskExecutionLogBase):
    task_id: int


class TaskExecutionLog(TaskExecutionLogBase):
    id: int
    task_id: int
    executed_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Scheduled Task Schemas
class ScheduledTaskBase(BaseModel):
    task_type: str
    payload: Dict[str, Any]
    scheduled_time: datetime
    recurrence_rule: Optional[str] = None  # For RRULE strings


class ScheduledTaskCreate(ScheduledTaskBase):
    user_id: int
    parent_task_id: Optional[int] = None


class ScheduledTaskUpdate(BaseModel):
    scheduled_time: Optional[datetime] = None
    payload: Optional[Dict[str, Any]] = None
    status: Optional[ScheduledTaskStatus] = None
    recurrence_rule: Optional[str] = None
    error_message: Optional[str] = None


class ScheduledTask(ScheduledTaskBase):
    id: int
    user_id: int
    status: ScheduledTaskStatus
    executed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    parent_task_id: Optional[int] = None
    execution_logs: List[TaskExecutionLog] = []

    model_config = ConfigDict(from_attributes=True)


class ScheduledTaskWithUser(ScheduledTask):
    user: User  # Nested user information


# Scheduled Update Schemas
class ScheduledUpdate(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ScheduledUpdateCreate(BaseModel):
    user_id: int
    update_type: str  # e.g., "product_description", "ab_test", "discount"
    target_id: int  # ID of the product, AB test, or discount
    new_value: str  # New description text, AB test config, or discount details
    scheduled_time: datetime


class ScheduledUpdateRead(BaseModel):
    id: int
    is_executed: bool
    executed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
