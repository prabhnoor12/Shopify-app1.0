from ...celery_async_app import celery_app
from my_app.database import AsyncSessionLocal
from my_app.services.scheduling_service import SchedulingService
from my_app.services.notification_service import NotificationService
from my_app.schemas.notification import EventType
from my_app.crud.user_crud import get_user
from my_app.models.scheduler import ScheduledTask, ScheduledTaskStatus
from sqlalchemy import select


@celery_app.task(bind=True)
async def run_due_scheduled_tasks(self):
    """
    Celery task to run all scheduled tasks that are due.
    """
    async with AsyncSessionLocal() as db:
        scheduling_service = SchedulingService(db)
        notification_service = NotificationService(db)

        processed_tasks = await scheduling_service.run_due_tasks()

        for task in processed_tasks:
            user = await get_user(db, user_id=task.user_id)
            if user:
                event_type = (
                    EventType.SCHEDULED_TASK_SUCCESS
                    if task.status == ScheduledTaskStatus.EXECUTED.value
                    else EventType.SCHEDULED_TASK_FAILURE
                )
                await notification_service.notify_event(
                    user_id=user.id,
                    event_type=event_type,
                    data={
                        "task_id": task.id,
                        "task_type": task.task_type,
                        "status": task.status,
                    },
                )


@celery_app.task(name="tasks.generate_recurring_tasks")
async def generate_recurring_tasks():
    """
    Celery task to generate future instances of recurring tasks.
    Runs periodically (e.g., once a day).
    """
    async with AsyncSessionLocal() as db:
        scheduling_service = SchedulingService(db)
        # Get all active recurring tasks (tasks with a recurrence_rule that are not cancelled)
        result = await db.execute(
            select(ScheduledTask).filter(
                ScheduledTask.recurrence_rule != None,
                ScheduledTask.status != ScheduledTaskStatus.CANCELLED.value,
            )
        )
        recurring_tasks = result.scalars().all()

        for task in recurring_tasks:
            await scheduling_service._handle_recurring_task(task)
