"""
Comprehensive tests for the CalenderService.

This test suite ensures that the CalenderService correctly fetches scheduled tasks
and transforms them into a calender-friendly event format for the frontend.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from my_app.services.calender_service import CalenderService
from my_app.schemas.scheduler import ScheduledTask
from my_app.schemas.calender import CalenderEvent
from my_app.models.scheduler import ScheduledTaskStatus


@pytest.fixture
def calender(mock_db_session: MagicMock) -> CalenderService:
    """Provides an instance of CalenderService with a mocked DB session."""
    # We need to patch the service it depends on
    with patch(
        "my_app.services.calender_service.SchedulingService"
    ) as MockSchedulingService:
        service_instance = CalenderService(db=mock_db_session)
        # Replace the real scheduling_service instance with a mock
        service_instance.scheduling_service = MockSchedulingService()
        return service_instance


@pytest.fixture
def mock_task_list() -> list[ScheduledTask]:
    """Provides a list of mock ScheduledTask schema objects."""
    time_now = datetime.utcnow()
    return [
        ScheduledTask(
            id=1,
            user_id=1,
            task_type="product_description_update",
            payload={"product_name": "Cool Shoes"},
            scheduled_time=time_now + timedelta(days=1),
            status=ScheduledTaskStatus.PENDING.value,
            created_at=time_now,
            execution_logs=[],
        ),
        ScheduledTask(
            id=2,
            user_id=1,
            task_type="ab_test_rotation",
            payload={"ab_test_name": "Homepage Test"},
            scheduled_time=time_now + timedelta(days=2),
            status=ScheduledTaskStatus.EXECUTED.value,
            created_at=time_now,
            executed_at=time_now + timedelta(days=2),
            execution_logs=[],
        ),
        ScheduledTask(
            id=3,
            user_id=1,
            task_type="unknown_task",
            payload={},
            scheduled_time=time_now + timedelta(days=3),
            status=ScheduledTaskStatus.FAILED.value,
            created_at=time_now,
            execution_logs=[],
        ),
    ]


class TestCalenderService:
    """
    Test suite for the CalenderService.
    """

    def test_get_calender_events(
        self, calender: CalenderService, mock_task_list: list[ScheduledTask]
    ):
        """
        Tests that scheduled tasks are correctly fetched and formatted into calender events.
        """
        user_id = 1
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30)

        # Configure the mock scheduling service to return our mock tasks
        calender.scheduling_service.get_scheduled_tasks.return_value = mock_task_list

        events = calender.get_calender_events(user_id, start_date, end_date)

        # Verify that the scheduling service was called correctly
        calender.scheduling_service.get_scheduled_tasks.assert_called_once_with(
            user_id=user_id, limit=1000
        )

        # Verify the transformation logic
        assert len(events) == len(mock_task_list)

        # Expected titles based on task type and payload
        expected_titles = [
            "Product Description Update",
            "Ab Test Rotation",
            "Unknown Task",
        ]

        for i, event in enumerate(events):
            task = mock_task_list[i]
            assert isinstance(event, CalenderEvent)
            assert event.id == task.id
            assert event.title == expected_titles[i]
            assert event.start == task.scheduled_time
            # Assuming events are instantaneous, so end time is same as start time
            assert event.end == task.scheduled_time
            assert event.extendedProps.status == task.status
            assert event.extendedProps.task_type == task.task_type

    def test_get_calender_events_no_tasks(self, calender: CalenderService):
        """
        Tests that an empty list is returned when no tasks are scheduled in the given range.
        """
        user_id = 1
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30)

        # Configure the mock to return an empty list
        calender.scheduling_service.get_scheduled_tasks.return_value = []

        events = calender.get_calender_events(user_id, start_date, end_date)

        # Verify that the scheduling service was called
        calender.scheduling_service.get_scheduled_tasks.assert_called_once_with(
            user_id=user_id, limit=1000
        )

        # Verify that the result is an empty list
        assert events == []
