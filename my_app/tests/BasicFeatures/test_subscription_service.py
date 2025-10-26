import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from ..models.subscription import Subscription, SubscriptionStatus
from ..models.plan import Plan  # Added Plan
from my_app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionUpdate,
)
from my_app.services.subscription_service import SubscriptionService
from my_app.core.pricing_config import PRICING_PLANS  # Import PRICING_PLANS
from fastapi import HTTPException


# Mock database session
@pytest.fixture
def mock_db_session():
    """Fixture for a mocked database session."""
    return MagicMock()


@pytest.fixture
def subscription_service(mock_db_session):
    """Fixture for SubscriptionService instance."""
    return SubscriptionService(mock_db_session)


# Mock settings for shopify.create_recurring_application_charge
@pytest.fixture(autouse=True)
def mock_settings():
    with patch(
        "my_app.services.subscription_service.get_settings"
    ) as mock_get_settings:
        mock_settings_instance = MagicMock()
        mock_settings_instance.SHOPIFY_BILLING_TEST_MODE = True
        mock_get_settings.return_value = mock_settings_instance
        yield


class TestSubscriptionService:
    def test_create_subscription_success(self, subscription_service, mock_db_session):
        # Arrange
        user_id = 1
        shop_id = 1
        shop_domain = "test.myshopify.com"
        access_token = "shpat_test_token"
        return_url = "https://app.example.com/callback"
        plan_id = 1
        subscription_create_schema = SubscriptionCreate(
            shop_id=shop_id, plan_id=plan_id
        )

        mock_plan = Plan(id=plan_id, name="basic", price=10.0)
        mock_db_session.query().filter().first.side_effect = [
            None,  # No existing active subscription
            mock_plan,  # Found plan
        ]

        mock_shopify_charge_response = {
            "recurring_application_charge": {
                "confirmation_url": "https://shopify.com/confirmation",
                "id": 12345,
            }
        }
        mock_shopify = MagicMock()
        mock_shopify.create_recurring_application_charge.return_value = (
            mock_shopify_charge_response
        )
        with patch("my_app.services.subscription_service.shopify", mock_shopify):
            with patch(
                "my_app.services.subscription_service.subscription_crud.create"
            ) as mock_crud_create_subscription:
                mock_crud_create_subscription.return_value = Subscription(
                    user_id=1,
                    shop_id=shop_id,
                    plan_id=plan_id,
                    shopify_charge_id=12345,
                    confirmation_url="https://shopify.com/confirmation",
                    status=SubscriptionStatus.PENDING,
                )
                # Act
                result = subscription_service.create_subscription(
                    user_id=user_id,
                    shop_domain=shop_domain,
                    access_token=access_token,
                    return_url=return_url,
                    subscription_create=subscription_create_schema,
                )

                # Assert
                assert result is not None
                assert result.user_id == user_id
                assert result.plan_id == plan_id
                assert result.status == SubscriptionStatus.PENDING
                assert result.shopify_charge_id == 12345
                assert result.confirmation_url == "https://shopify.com/confirmation"
                mock_crud_create_subscription.assert_called_once()
                # Verify that get_subscription_by_user and get_plan were called
                assert mock_db_session.query().filter().first.call_count == 2

    def test_create_subscription_user_has_active_subscription(
        self, subscription_service, mock_db_session
    ):
        # Arrange
        user_id = 1
        shop_id = 1
        shop_domain = "test.myshopify.com"
        access_token = "shpat_test_token"
        return_url = "https://app.example.com/callback"
        plan_id = 1
        subscription_create_schema = SubscriptionCreate(
            shop_id=shop_id, plan_id=plan_id
        )

        mock_existing_subscription = Subscription(
            id=1, user_id=user_id, status=SubscriptionStatus.ACTIVE
        )
        mock_db_session.query().filter().first.return_value = (
            mock_existing_subscription  # Existing active subscription
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            subscription_service.create_subscription(
                user_id=user_id,
                shop_domain=shop_domain,
                access_token=access_token,
                return_url=return_url,
                subscription_create=subscription_create_schema,
            )
        assert exc_info.value.status_code == 400
        assert "User already has an active subscription." in exc_info.value.detail

    def test_update_subscription_plan_change_success(
        self, subscription_service, mock_db_session
    ):
        # Arrange
        subscription_id = 1
        shop_domain = "test.myshopify.com"
        access_token = "shpat_test_token"
        return_url = "https://app.example.com/callback"
        new_plan_id = 2
        subscription_update_schema = SubscriptionUpdate(plan_id=new_plan_id)

        mock_current_subscription = Subscription(
            id=subscription_id,
            plan_id=1,
            shopify_charge_id=111,
            status=SubscriptionStatus.ACTIVE,
        )
        mock_old_plan = Plan(id=1, name="basic", price=10.0)
        mock_new_plan = Plan(id=new_plan_id, name="advanced", price=20.0)

        # Mock calls for get_subscription, get_plan (old), get_plan (new)
        mock_db_session.query().filter().first.side_effect = [
            mock_current_subscription,  # get_subscription
            mock_old_plan,  # get_plan (old)
            mock_new_plan,  # get_plan (new)
        ]

        mock_shopify_charge_response = {
            "recurring_application_charge": {
                "confirmation_url": "https://shopify.com/new_confirmation",
                "id": 222,
            }
        }
        mock_shopify = MagicMock()
        mock_shopify.create_recurring_application_charge.return_value = (
            mock_shopify_charge_response
        )
        with patch("my_app.services.subscription_service.shopify", mock_shopify):
            with patch(
                "my_app.services.subscription_service.subscription_crud.update"
            ) as mock_crud_update_subscription:
                mock_crud_update_subscription.return_value = Subscription(
                    id=subscription_id,
                    plan_id=new_plan_id,
                    shopify_charge_id=222,
                    confirmation_url="https://shopify.com/new_confirmation",
                    status=SubscriptionStatus.PENDING,
                )
                # Act
                result = subscription_service.update_subscription(
                    subscription_id=subscription_id,
                    shop_domain=shop_domain,
                    access_token=access_token,
                    return_url=return_url,
                    subscription_update=subscription_update_schema,
                )

                # Assert
                assert result is not None
                assert "confirmation_url" in result
                assert (
                    result["confirmation_url"] == "https://shopify.com/new_confirmation"
                )
                assert result["subscription"].plan_id == new_plan_id
                assert result["subscription"].status == SubscriptionStatus.PENDING
                mock_crud_update_subscription.assert_called_once()
                assert (
                    mock_db_session.query().filter().first.call_count == 3
                )  # get_subscription, get_plan (old), get_plan (new)

    def test_cancel_subscription_success(self, subscription_service, mock_db_session):
        # Arrange
        subscription_id = 1
        shop_domain = "test.myshopify.com"
        access_token = "shpat_test_token"

        mock_subscription = Subscription(
            id=subscription_id, shopify_charge_id=123, status=SubscriptionStatus.ACTIVE
        )
        mock_db_session.query().filter().first.return_value = mock_subscription

        mock_shopify = MagicMock()
        with patch("my_app.services.subscription_service.shopify", mock_shopify):
            with patch(
                "my_app.services.subscription_service.subscription_crud.update"
            ) as mock_crud_update_subscription:
                mock_crud_update_subscription.return_value = Subscription(
                    id=subscription_id,
                    shopify_charge_id=123,
                    status=SubscriptionStatus.CANCELED,
                    updated_at=datetime.utcnow(),
                )
                # Act
                result = subscription_service.cancel_subscription(
                    subscription_id=subscription_id,
                    shop_domain=shop_domain,
                    access_token=access_token,
                )

                # Assert
                assert result is not None
                assert result.status == SubscriptionStatus.CANCELED
                mock_shopify.cancel_recurring_application_charge.assert_called_once_with(
                    shop_domain=shop_domain,
                    access_token=access_token,
                    charge_id=mock_subscription.shopify_charge_id,
                )
                mock_crud_update_subscription.assert_called_once()

    def test_get_subscription_status_active(
        self, subscription_service, mock_db_session
    ):
        # Arrange
        user_id = 1
        mock_plan = Plan(id=1, name="basic")
        mock_subscription = Subscription(
            id=1,
            user_id=user_id,
            status=SubscriptionStatus.ACTIVE,
            plan=mock_plan,  # Assign the mock_plan object
            trial_ends_at=None,
            current_billing_period_starts_at=datetime(2023, 1, 1),
            current_billing_period_ends_at=datetime(2023, 2, 1),
            shopify_charge_id=123,
            confirmation_url="http://example.com/confirm",
        )
        mock_db_session.query().filter().order_by().first.return_value = (
            mock_subscription
        )

        # Act
        status_info = subscription_service.get_subscription_status(user_id)

        # Assert
        assert status_info is not None
        assert status_info["status"] == SubscriptionStatus.ACTIVE.value
        assert status_info["plan"] == "basic"
        assert status_info["plan_name"] == PRICING_PLANS["basic"]["name"]
        assert status_info["shopify_charge_id"] == 123

    def test_get_subscription_status_no_subscription(
        self, subscription_service, mock_db_session
    ):
        # Arrange
        user_id = 1
        mock_db_session.query().filter().order_by().first.return_value = (
            None  # No subscription found
        )

        # Act
        status_info = subscription_service.get_subscription_status(user_id)

        # Assert
        assert status_info is not None
        assert status_info["status"] == "no_subscription"
        assert status_info["plan"] == "none"
