from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from ..models.scheduler import ScheduledTask, ScheduledTaskStatus, TaskExecutionLog
from ..models.team import TeamMember
from ..models.user import User

from .. import schemas


# Task Execution Log CRUD


def create_task_execution_log(
    db: Session, log_create: schemas.TaskExecutionLogCreate
) -> TaskExecutionLog:
    db_log = TaskExecutionLog(**log_create.dict())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


def get_execution_logs_for_task(db: Session, task_id: int) -> List[TaskExecutionLog]:
    return (
        db.query(TaskExecutionLog)
        .filter(TaskExecutionLog.task_id == task_id)
        .order_by(TaskExecutionLog.executed_at.desc())
        .all()
    )


# Scheduled Task CRUD


def get_scheduled_task(db: Session, task_id: int) -> Optional[ScheduledTask]:
    return (
        db.query(ScheduledTask)
        .options(joinedload(ScheduledTask.user))
        .filter(ScheduledTask.id == task_id)
        .first()
    )


def get_due_scheduled_tasks(db: Session, as_of: datetime) -> List[ScheduledTask]:
    return (
        db.query(ScheduledTask)
        .filter(
            ScheduledTask.scheduled_time <= as_of,
            ScheduledTask.status == ScheduledTaskStatus.PENDING,
        )
        .all()
    )


def get_scheduled_tasks_by_user(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    status: Optional[ScheduledTaskStatus] = None,
) -> List[ScheduledTask]:
    query = db.query(ScheduledTask).filter(ScheduledTask.user_id == user_id)
    if status:
        query = query.filter(ScheduledTask.status == status)
    return query.options(joinedload(ScheduledTask.user)).offset(skip).limit(limit).all()


def get_scheduled_tasks_by_user_in_range(
    db: Session, user_id: int, start_date: datetime, end_date: datetime
) -> List[ScheduledTask]:
    return (
        db.query(ScheduledTask)
        .filter(
            ScheduledTask.user_id == user_id,
            ScheduledTask.scheduled_time >= start_date,
            ScheduledTask.scheduled_time <= end_date,
        )
        .options(joinedload(ScheduledTask.user))
        .all()
    )


def get_scheduled_tasks_for_team_in_range(
    db: Session,
    team_id: int,
    start_date: datetime,
    end_date: datetime,
    user_id: Optional[int] = None,
    role_id: Optional[int] = None,
) -> List[ScheduledTask]:
    query = (
        db.query(ScheduledTask)
        .join(User)
        .join(TeamMember, TeamMember.user_id == User.id)
        .filter(
            TeamMember.team_id == team_id,
            ScheduledTask.scheduled_time >= start_date,
            ScheduledTask.scheduled_time <= end_date,
        )
    )

    if user_id:
        query = query.filter(ScheduledTask.user_id == user_id)

    if role_id:
        query = query.filter(TeamMember.role_id == role_id)

    return query.options(joinedload(ScheduledTask.user)).all()


def create_scheduled_task(
    db: Session, task: schemas.ScheduledTaskCreate
) -> ScheduledTask:
    db_task = ScheduledTask(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def update_scheduled_task(
    db: Session, task_id: int, task_update: schemas.ScheduledTaskUpdate
) -> Optional[ScheduledTask]:
    db_task = get_scheduled_task(db, task_id)
    if db_task:
        update_data = task_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_task, key, value)
        db.commit()
        db.refresh(db_task)
    return db_task
