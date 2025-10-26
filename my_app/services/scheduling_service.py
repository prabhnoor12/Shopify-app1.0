import asyncio
from datetime import datetime, UTC
from typing import Optional, List, Dict, Any, Callable, Awaitable
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from dateutil.rrule import rrulestr

from ..models.scheduler import ScheduledTask, ScheduledTaskStatus
from ..services.ab_testing_service import ABTestingService
from ..crud import scheduler_crud, product_crud, user_crud
from .. import schemas


class SchedulingService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        ab_testing_service: ABTestingService,
    ):
        self.session_factory = session_factory
        self.ab_testing_service = ab_testing_service
        self._task_handlers: Dict[
            str, Callable[[AsyncSession, ScheduledTask], Awaitable[None]]
        ] = {
            "product_description_update": self._execute_product_description_update,
            "ab_test_rotation": self._execute_ab_test_rotation,
        }

    async def schedule_task(
        self,
        user_id: int,
        task_type: str,
        scheduled_time: datetime,
        payload: Dict[str, Any],
        recurrence_rule: Optional[str] = None,
        parent_task_id: Optional[int] = None,
    ) -> schemas.ScheduledTask:
        async with self.session_factory() as session:
            task_create = schemas.ScheduledTaskCreate(
                user_id=user_id,
                task_type=task_type,
                scheduled_time=scheduled_time,
                payload=payload,
                recurrence_rule=recurrence_rule,
                parent_task_id=parent_task_id,
            )
            task = scheduler_crud.create_scheduled_task(session, task=task_create)
            await session.commit()
            await session.refresh(task)
            return task

    async def _process_task(self, task: ScheduledTask) -> ScheduledTask:
        async with self.session_factory() as session:
            log_status = ScheduledTaskStatus.EXECUTED.value
            log_message = f"Task {task.id} executed successfully."
            try:
                handler = self._task_handlers.get(task.task_type)
                if not handler:
                    raise ValueError(f"Unknown task type: {task.task_type}")

                await handler(session, task)

                updated_task = scheduler_crud.update_scheduled_task(
                    session,
                    task.id,
                    schemas.ScheduledTaskUpdate(
                        status=ScheduledTaskStatus.EXECUTED,
                        executed_at=datetime.now(UTC),
                    ),
                )

                if task.recurrence_rule:
                    await self._handle_recurring_task(session, task)

            except Exception as e:
                await session.rollback()
                log_status = ScheduledTaskStatus.FAILED.value
                log_message = str(e)
                error_message = f"Failed to execute task {task.id}: {e}"
                updated_task = scheduler_crud.update_scheduled_task(
                    session,
                    task.id,
                    schemas.ScheduledTaskUpdate(
                        status=ScheduledTaskStatus.FAILED, error_message=error_message
                    ),
                )
            finally:
                log_create = schemas.TaskExecutionLogCreate(
                    task_id=task.id, status=log_status, log=log_message
                )
                scheduler_crud.create_task_execution_log(session, log_create=log_create)
                await session.commit()

            return updated_task

    async def run_due_tasks(self) -> List[ScheduledTask]:
        async with self.session_factory() as session:
            now = datetime.now(UTC)
            due_tasks = await scheduler_crud.get_due_scheduled_tasks(session, now)

        processed_tasks = await asyncio.gather(
            *(self._process_task(task) for task in due_tasks)
        )

        return processed_tasks

    async def _handle_recurring_task(self, session: AsyncSession, task: ScheduledTask):
        rule = rrulestr(task.recurrence_rule, dtstart=task.scheduled_time)
        next_occurrence = rule.after(datetime.now(UTC))

        if next_occurrence:
            existing_task = await scheduler_crud.get_task_by_parent_and_time(
                session, task.id, next_occurrence
            )

            if not existing_task:
                await self.schedule_task(
                    user_id=task.user_id,
                    task_type=task.task_type,
                    scheduled_time=next_occurrence,
                    payload=task.payload,
                    recurrence_rule=task.recurrence_rule,
                    parent_task_id=task.id,
                )

    async def _execute_product_description_update(
        self, session: AsyncSession, task: ScheduledTask
    ):
        product_id = task.payload.get("product_id")
        new_description = task.payload.get("new_description")

        if not product_id or not new_description:
            raise ValueError(
                "Payload missing product_id or new_description for product_description_update"
            )

        product = await product_crud.get_product(db=session, product_id=product_id)
        if product:
            product.body_html = new_description
            session.add(product)
        else:
            raise ValueError("Product not found")

    async def _execute_ab_test_rotation(
        self, session: AsyncSession, task: ScheduledTask
    ):
        ab_test_id = task.payload.get("ab_test_id")
        user_id = task.payload.get("user_id")

        if not ab_test_id or not user_id:
            raise ValueError(
                "Payload missing ab_test_id or user_id for ab_test_rotation"
            )

        user = await user_crud.get_user(db=session, user_id=user_id)
        if user:
            # Re-instantiate ABTestingService with the task-specific session
            ab_testing_service = ABTestingService(session)
            await ab_testing_service.rotate_and_update_shopify(ab_test_id, user)
        else:
            raise ValueError(f"User with ID {user_id} not found for AB test rotation")

    async def get_scheduled_tasks(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
    ) -> List[schemas.ScheduledTask]:
        async with self.session_factory() as session:
            db_status = ScheduledTaskStatus(status) if status else None
            return await scheduler_crud.get_scheduled_tasks_by_user(
                db=session, user_id=user_id, skip=skip, limit=limit, status=db_status
            )

    async def get_scheduled_tasks_in_range(
        self, user_id: int, start_date: datetime, end_date: datetime
    ) -> List[schemas.ScheduledTask]:
        async with self.session_factory() as session:
            return await scheduler_crud.get_scheduled_tasks_by_user_in_range(
                db=session,
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
            )

    async def cancel_scheduled_task(self, task_id: int, user_id: int) -> bool:
        async with self.session_factory() as session:
            task = await scheduler_crud.get_scheduled_task(db=session, task_id=task_id)
            if (
                not task
                or task.user_id != user_id
                or task.status != ScheduledTaskStatus.PENDING
            ):
                return False

            updated_task = scheduler_crud.update_scheduled_task(
                db=session,
                task_id=task_id,
                task_update=schemas.ScheduledTaskUpdate(
                    status=ScheduledTaskStatus.CANCELLED
                ),
            )
            await session.commit()
            return updated_task is not None
