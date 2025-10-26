from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from dateutil.rrule import rrulestr

from .scheduling_service import SchedulingService, ScheduledTaskStatus
from .. import schemas


class CalenderService:
    """
    Service to provide data formatted for a calender frontend.
    """

    def __init__(self, db: Session):
        self.db = db
        self.scheduling_service = SchedulingService(db)

    def get_calender_events(
        self, user_id: int, start_date: datetime, end_date: datetime
    ) -> List[schemas.CalenderEvent]:
        """
        Fetches scheduled tasks within a date range and formats them as calender events,
        including occurrences of recurring tasks.
        """
        tasks = self.scheduling_service.get_scheduled_tasks(
            user_id=user_id, limit=1000
        )  # Get all tasks to check for recurrence

        calender_events: List[schemas.CalenderEvent] = []
        for task in tasks:
            if task.recurrence_rule:
                rule = rrulestr(task.recurrence_rule, dtstart=task.scheduled_time)
                occurrences = rule.between(start_date, end_date)
                for occ in occurrences:
                    event = self._format_task_as_event(task, override_date=occ)
                    calender_events.append(event)
            elif start_date <= task.scheduled_time <= end_date:
                event = self._format_task_as_event(task)
                calender_events.append(event)

        return calender_events

    def _format_task_as_event(
        self, task: schemas.ScheduledTask, override_date: Optional[datetime] = None
    ) -> schemas.CalenderEvent:
        """
        Transforms a ScheduledTask object into a CalenderEvent object.
        """
        event_time = override_date or task.scheduled_time
        title = self._get_event_title(task)
        color = self._get_event_color(task.status)

        return schemas.CalenderEvent(
            id=task.id,
            title=title,
            start=event_time,
            end=event_time,  # Tasks are instantaneous
            extendedProps=schemas.CalenderEventExtendedProps(
                status=task.status,
                task_type=task.task_type,
                payload=task.payload,
                error_message=task.error_message,
                recurrence_rule=task.recurrence_rule,
            ),
            color=color,
        )

    def _get_event_title(self, task: schemas.ScheduledTask) -> str:
        """
        Generates a user-friendly title for the calender event.
        """
        title = task.task_type.replace("_", " ").title()
        if "product_id" in task.payload:
            title += f" (Product: {task.payload['product_id']})"
        if "ab_test_id" in task.payload:
            title += f" (A/B Test: {task.payload['ab_test_id']})"
        return title

    def _get_event_color(self, status: str) -> str:
        """
        Assigns a color based on the task status for frontend display.
        """
        if status == ScheduledTaskStatus.PENDING.value:
            return "#3B82F6"  # Blue
        elif status == ScheduledTaskStatus.EXECUTED.value:
            return "#10B981"  # Green
        elif status == ScheduledTaskStatus.FAILED.value:
            return "#EF4444"  # Red
        elif status == ScheduledTaskStatus.CANCELLED.value:
            return "#6B7280"  # Gray
        else:
            return "#A1A1AA"  # Default Gray
