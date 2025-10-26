"""
Comprehensive tests for the SchedulingService.

This test suite covers all public methods in SchedulingService, ensuring that task scheduling,
execution logic, and state management are handled correctly. It mocks the CRUD layer
and external service dependencies to isolate the service's business logic.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, UTC

from my_app.services.scheduling_service import SchedulingService
from my_app.models.scheduler import ScheduledTask, ScheduledTaskStatus
from my_app.models.shop import ShopifyUser
from my_app.models.product import Product


@pytest.fixture
def scheduling_service(mock_db_session: MagicMock) -> SchedulingService:
    """Provides an instance of SchedulingService with a mocked DB session."""
    return SchedulingService(db=mock_db_session)


@pytest.fixture
def mock_scheduled_task() -> ScheduledTask:
    """Provides a mock ScheduledTask object."""
    task = MagicMock(spec=ScheduledTask)
    task.id = 1
    task.user_id = 1
    task.task_type = "product_description_update"
    task.payload = {"product_id": 101, "new_description": "New shiny description"}
    task.status = ScheduledTaskStatus.PENDING
    task.recurrence_rule = None
    return task


@pytest.fixture
def mock_user() -> ShopifyUser:
    """Provides a mock ShopifyUser object."""
    user = MagicMock(spec=ShopifyUser)
    user.id = 1
    user.shop_url = "test-shop.myshopify.com"
    user.access_token = "test-token"
    return user


@pytest.fixture
def mock_product() -> Product:
    """Provides a mock Product object."""
    product = MagicMock(spec=Product)
    product.id = 1
    product.shopify_product_id = 101
    return product


@patch("my_app.services.scheduling_service.scheduler_crud")
class TestSchedulingService:
    """
    Test suite for the SchedulingService.
    Patches the scheduler_crud module to isolate service logic from data access logic.
    """

    def test_schedule_task(
        self, mock_crud: MagicMock, scheduling_service: SchedulingService
    ):
        """
        Tests that a task is correctly scheduled by calling the CRUD layer.
        """
        user_id = 1
        task_type = "product_description_update"
        scheduled_time = datetime.now(UTC) + timedelta(days=1)
        payload = {"product_id": 101, "description": "New description"}

        mock_crud.create_scheduled_task.return_value = MagicMock(spec=ScheduledTask)

        result = scheduling_service.schedule_task(
            user_id, task_type, scheduled_time, payload
        )

        mock_crud.create_scheduled_task.assert_called_once()
        call_args = mock_crud.create_scheduled_task.call_args[1]["task"]
        assert call_args.user_id == user_id
        assert call_args.task_type == task_type
        assert call_args.scheduled_time == scheduled_time
        assert call_args.payload == payload
        assert isinstance(result, ScheduledTask)

    @pytest.mark.asyncio
    async def test_run_due_tasks_product_update_success(
        self,
        mock_crud: MagicMock,
        scheduling_service: SchedulingService,
        mock_scheduled_task: ScheduledTask,
        mock_user: ShopifyUser,
        mock_product: Product,
    ):
        """
        Tests the successful execution of a due product description update task.
        """
        mock_crud.get_due_scheduled_tasks.return_value = [mock_scheduled_task]

        with (
            patch(
                "my_app.services.scheduling_service.product_crud"
            ) as mock_product_crud,
            patch("my_app.services.scheduling_service.user_crud") as mock_user_crud,
        ):
            mock_product_crud.get_product.return_value = mock_product
            mock_user_crud.get_user.return_value = mock_user

            await scheduling_service.run_due_tasks()

            mock_crud.get_due_scheduled_tasks.assert_called_once()
            mock_product_crud.get_product.assert_called_once_with(
                db=scheduling_service.db,
                product_id=mock_scheduled_task.payload["product_id"],
            )

            mock_crud.update_scheduled_task.assert_called_once()
            update_args = mock_crud.update_scheduled_task.call_args[0]
            assert update_args[1] == mock_scheduled_task.id
            assert update_args[2].status == ScheduledTaskStatus.EXECUTED

    @pytest.mark.asyncio
    async def test_run_due_tasks_execution_fails(
        self,
        mock_crud: MagicMock,
        scheduling_service: SchedulingService,
        mock_scheduled_task: ScheduledTask,
    ):
        """
        Tests that a task's status is set to FAILED when execution raises an exception.
        """
        mock_crud.get_due_scheduled_tasks.return_value = [mock_scheduled_task]
        error_message = "Product not found"

        with patch(
            "my_app.services.scheduling_service.product_crud"
        ) as mock_product_crud:
            mock_product_crud.get_product.return_value = (
                None  # Simulate product not found
            )

            await scheduling_service.run_due_tasks()

            mock_crud.update_scheduled_task.assert_called_once()
            update_args = mock_crud.update_scheduled_task.call_args[0]
            assert update_args[1] == mock_scheduled_task.id
            assert update_args[2].status == ScheduledTaskStatus.FAILED
            assert error_message in update_args[2].error_message

    def test_get_scheduled_tasks(
        self, mock_crud: MagicMock, scheduling_service: SchedulingService
    ):
        """
        Tests retrieving scheduled tasks for a user.
        """
        user_id = 1
        mock_crud.get_scheduled_tasks_by_user.return_value = [
            MagicMock(spec=ScheduledTask)
        ]

        tasks = scheduling_service.get_scheduled_tasks(user_id=user_id, limit=10)

        mock_crud.get_scheduled_tasks_by_user.assert_called_once_with(
            db=scheduling_service.db, user_id=user_id, skip=0, limit=10, status=None
        )
        assert len(tasks) == 1

    def test_get_scheduled_tasks_in_range(
        self, mock_crud: MagicMock, scheduling_service: SchedulingService
    ):
        """
        Tests retrieving scheduled tasks for a user within a date range.
        """
        user_id = 1
        start_date = datetime.now(UTC)
        end_date = start_date + timedelta(days=30)
        mock_crud.get_scheduled_tasks_by_user_in_range.return_value = [
            MagicMock(spec=ScheduledTask)
        ]

        tasks = scheduling_service.get_scheduled_tasks_in_range(
            user_id, start_date, end_date
        )

        mock_crud.get_scheduled_tasks_by_user_in_range.assert_called_once_with(
            db=scheduling_service.db,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
        )
        assert len(tasks) == 1

    def test_cancel_scheduled_task(
        self,
        mock_crud: MagicMock,
        scheduling_service: SchedulingService,
        mock_scheduled_task: ScheduledTask,
    ):
        """
        Tests cancelling a pending scheduled task.
        """
        task_id = 1
        user_id = 1
        mock_crud.get_scheduled_task.return_value = mock_scheduled_task
        mock_crud.update_scheduled_task.return_value = mock_scheduled_task

        result = scheduling_service.cancel_scheduled_task(
            task_id=task_id, user_id=user_id
        )

        mock_crud.get_scheduled_task.assert_called_once_with(
            db=scheduling_service.db, task_id=task_id
        )
        update_call_args = mock_crud.update_scheduled_task.call_args[1]["task_update"]
        assert update_call_args.status == ScheduledTaskStatus.CANCELLED
        assert result is True
