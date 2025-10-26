from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import schemas, crud
from ..database import get_db
from ..dependencies.auth import get_current_user
from ..models.user import User
from ..services.scheduling_service import SchedulingService

router = APIRouter()


@router.post("/schedule", response_model=schemas.ScheduledTask)
def create_scheduled_task(
    task: schemas.ScheduledTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Ensure the task is for the current user
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot schedule tasks for other users",
        )

    scheduling_service = SchedulingService(db)
    return scheduling_service.schedule_task(
        user_id=current_user.id,
        task_type=task.task_type,
        scheduled_time=task.scheduled_time,
        payload=task.payload,
    )


@router.get("/schedule", response_model=List[schemas.ScheduledTask])
def get_scheduled_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
):
    scheduling_service = SchedulingService(db)
    return scheduling_service.get_scheduled_tasks(
        user_id=current_user.id, skip=skip, limit=limit, status=status
    )


@router.get("/schedule/{task_id}", response_model=schemas.ScheduledTask)
def get_scheduled_task_by_id(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scheduling_service = SchedulingService(db)
    task = crud.scheduler_crud.get_scheduled_task(db, task_id)
    if not task or task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled task not found or not authorized",
        )
    return schemas.ScheduledTask.from_orm(task)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled task not found"
        )
    return task


@router.put("/schedule/{task_id}", response_model=schemas.ScheduledTask)
def update_scheduled_task(
    task_id: int,
    task_update: schemas.ScheduledTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scheduling_service = SchedulingService(db)
    # First, check if the task belongs to the current user
    existing_task = crud.scheduler_crud.get_scheduled_task(db, task_id)
    if not existing_task or existing_task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this task",
        )

    updated_task = crud.scheduler_crud.update_scheduled_task(db, task_id, task_update)
    if not updated_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled task not found"
        )
    return updated_task


@router.delete("/schedule/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scheduled_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scheduling_service = SchedulingService(db)
    if not scheduling_service.cancel_scheduled_task(
        task_id=task_id, user_id=current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled task not found or not authorized to cancel",
        )
    return
