import pytest
from unittest.mock import MagicMock
from my_app.models.usage import Usage
from my_app.models.subscription import Subscription
from my_app.models.shop import ShopifyUser
from my_app.services.usage_service import UsageService
from my_app.core.pricing_config import PRICING_PLANS, USAGE_CHARGE_RATES
import requests


@pytest.fixture
def mock_db_session():
    """Fixture for a mocked database session."""
    return MagicMock()


@pytest.fixture
def usage_service(mock_db_session):
    """Fixture for UsageService instance."""
    return UsageService(mock_db_session)


@pytest.fixture
def mock_usage_crud(mocker):
    """Fixture for mocking usage CRUD functions."""
    return mocker.patch("my_app.services.usage_service.crud.usage")


@pytest.fixture
def mock_shop_crud(mocker):
    """Fixture for mocking shop CRUD functions."""
    return mocker.patch("my_app.services.usage_service.crud_shop")


@pytest.fixture
def mock_subscription_crud(mocker):
    """Fixture for mocking subscription CRUD functions."""
    return mocker.patch("my_app.services.usage_service.crud_subscription")


@pytest.fixture
def mock_usage_event_crud(mocker):
    """Fixture for mocking usage_event CRUD functions."""
    return mocker.patch("my_app.services.usage_service.crud_usage_event")


@pytest.fixture
def mock_shopify_client(mocker):
    """Fixture for mocking the ShopifyClient."""
    mock_client_instance = MagicMock()
    mocker.patch(
        "my_app.services.usage_service.get_shopify_client",
        return_value=mock_client_instance,
    )
    return mock_client_instance


class TestGetUserUsage:
    def test_get_user_usage_success(self, usage_service, mock_usage_crud):
        # Arrange
        user_id = 1
        expected_usage = {"descriptions_generated_short": 10}
        mock_usage_crud.get_total_usage_by_user.return_value = expected_usage

        # Act
        result = usage_service.get_user_usage(user_id)

        # Assert
        assert result == expected_usage
        mock_usage_crud.get_total_usage_by_user.assert_called_once_with(
            usage_service.db, user_id=user_id
        )

    def test_get_user_usage_not_found(self, usage_service, mock_usage_crud):
        # Arrange
        user_id = 999
        mock_usage_crud.get_total_usage_by_user.return_value = {}

        # Act
        result = usage_service.get_user_usage(user_id)

        # Assert
        assert result == {}
        mock_usage_crud.get_total_usage_by_user.assert_called_once_with(
            usage_service.db, user_id=user_id
        )


class TestGetTeamUsage:
    def test_get_team_usage_success(self, usage_service, mock_usage_crud):
        # Arrange
        team_id = 1
        expected_usage = {"descriptions_generated_short": 50}
        mock_usage_crud.get_total_usage_by_team.return_value = expected_usage

        # Act
        result = usage_service.get_team_usage(team_id)

        # Assert
        assert result == expected_usage
        mock_usage_crud.get_total_usage_by_team.assert_called_once_with(
            usage_service.db, team_id=team_id
        )

    def test_get_team_usage_not_found(self, usage_service, mock_usage_crud):
        # Arrange
        team_id = 999
        mock_usage_crud.get_total_usage_by_team.return_value = {}

        # Act
        result = usage_service.get_team_usage(team_id)

        # Assert
        assert result == {}
        mock_usage_crud.get_total_usage_by_team.assert_called_once_with(
            usage_service.db, team_id=team_id
        )


class TestRecordUsage:
    @pytest.fixture
    def setup_mocks(
        self,
        mock_usage_crud,
        mock_shop_crud,
        mock_subscription_crud,
        mock_usage_event_crud,
        mock_shopify_client,
    ):
        # Common setup for record_usage tests
        mock_shop_user = ShopifyUser(id=1, shop_domain="test.myshopify.com")
        mock_shop_crud.get_user_by_domain.return_value = mock_shop_user

        mock_db_usage = Usage(id=1, user_id=1, descriptions_generated_short=0)
        mock_usage_crud.get_usage_record.return_value = mock_db_usage

        return (
            mock_usage_crud,
            mock_shop_crud,
            mock_subscription_crud,
            mock_usage_event_crud,
            mock_shopify_client,
            mock_db_usage,
        )

    def test_record_usage_free_plan_no_charge(self, usage_service, setup_mocks):
        # Arrange
        (
            mock_usage_crud,
            mock_shop_crud,
            _,
            mock_usage_event_crud,
            mock_shopify_client,
            _,
        ) = setup_mocks

        # Act
        usage_service.record_usage(
            user_id=1,
            shop_domain="test.myshopify.com",
            access_token="token",
            subscription_plan="free",
            feature_name="descriptions_generated_short",
            quantity=1,
        )

        # Assert
        mock_usage_crud.update_usage_record.assert_called_once()
        mock_usage_event_crud.create_usage_event.assert_called_once()
        mock_shopify_client.create_usage_charge.assert_not_called()

    def test_record_usage_paid_plan_charges_on_each_use(
        self, usage_service, setup_mocks
    ):
        # Arrange
        (
            mock_usage_crud,
            _,
            mock_subscription_crud,
            mock_usage_event_crud,
            mock_shopify_client,
            mock_db_usage,
        ) = setup_mocks
        mock_db_usage.descriptions_generated_short = 0  # Below limit

        mock_active_subscription = Subscription(
            id=1, user_id=1, shopify_charge_id=12345, status="active"
        )
        mock_subscription_crud.get_active_subscription_by_user_and_shop_domain.return_value = mock_active_subscription

        feature_name = "descriptions_generated_short"
        quantity = 1

        # Act
        usage_service.record_usage(
            user_id=1,
            shop_domain="test.myshopify.com",
            access_token="token",
            subscription_plan="basic",
            feature_name=feature_name,
            quantity=quantity,
        )

        # Assert
        mock_usage_crud.update_usage_record.assert_called_once()
        mock_usage_event_crud.create_usage_event.assert_called_once()
        mock_shopify_client.create_usage_charge.assert_called_once_with(
            recurring_charge_id=mock_active_subscription.shopify_charge_id,
            description=f"{feature_name} usage",
            price=USAGE_CHARGE_RATES[feature_name] * quantity,
            quantity=quantity,
        )

    def test_record_usage_paid_plan_exceeds_limit_with_charge(
        self, usage_service, setup_mocks
    ):
        # Arrange
        (
            mock_usage_crud,
            _,
            mock_subscription_crud,
            mock_usage_event_crud,
            mock_shopify_client,
            mock_db_usage,
        ) = setup_mocks

        subscription_plan = "basic"
        feature_name = "descriptions_generated_short"
        quantity = 1

        # Set current usage to be exactly at the free limit
        mock_db_usage.descriptions_generated_short = PRICING_PLANS[subscription_plan][
            "features"
        ][feature_name]

        mock_active_subscription = Subscription(
            id=1, user_id=1, shopify_charge_id=12345, status="active"
        )
        mock_subscription_crud.get_active_subscription_by_user_and_shop_domain.return_value = mock_active_subscription

        # Act
        usage_service.record_usage(
            user_id=1,
            shop_domain="test.myshopify.com",
            access_token="token",
            subscription_plan=subscription_plan,
            feature_name=feature_name,
            quantity=quantity,
        )

        # Assert
        mock_usage_crud.update_usage_record.assert_called_once()
        mock_usage_event_crud.create_usage_event.assert_called_once()
        mock_shopify_client.create_usage_charge.assert_called_once_with(
            recurring_charge_id=mock_active_subscription.shopify_charge_id,
            description=f"{feature_name} usage",
            price=USAGE_CHARGE_RATES[feature_name] * quantity,
            quantity=quantity,
        )

    def test_record_usage_invalid_plan(self, usage_service, setup_mocks, caplog):
        # Arrange
        (mock_usage_crud, _, _, mock_usage_event_crud, mock_shopify_client, _) = (
            setup_mocks
        )

        # Act
        usage_service.record_usage(
            user_id=1,
            shop_domain="test.myshopify.com",
            access_token="token",
            subscription_plan="invalid_plan",
            feature_name="descriptions_generated_short",
            quantity=1,
        )

        # Assert
        mock_shopify_client.create_usage_charge.assert_not_called()
        assert "Invalid subscription plan 'invalid_plan'" in caplog.text

    def test_record_usage_shop_not_found(self, usage_service, setup_mocks, caplog):
        # Arrange
        (_, mock_shop_crud, _, _, mock_shopify_client, _) = setup_mocks
        mock_shop_crud.get_user_by_domain.return_value = None

        # Act
        usage_service.record_usage(
            user_id=1,
            shop_domain="test.myshopify.com",
            access_token="token",
            subscription_plan="basic",
            feature_name="descriptions_generated_short",
            quantity=1,
        )

        # Assert
        mock_shopify_client.create_usage_charge.assert_not_called()
        assert "Shop user not found for domain" in caplog.text

    def test_record_usage_shopify_api_fails_with_retry(
        self, usage_service, setup_mocks, caplog
    ):
        # Arrange
        (
            mock_usage_crud,
            _,
            mock_subscription_crud,
            _,
            mock_shopify_client,
            mock_db_usage,
        ) = setup_mocks

        subscription_plan = "basic"
        feature_name = "descriptions_generated_short"

        mock_db_usage.descriptions_generated_short = (
            PRICING_PLANS[subscription_plan]["features"][feature_name] + 1
        )

        mock_active_subscription = Subscription(
            id=1, user_id=1, shopify_charge_id=12345, status="active"
        )
        mock_subscription_crud.get_active_subscription_by_user_and_shop_domain.return_value = mock_active_subscription

        mock_shopify_client.create_usage_charge.side_effect = (
            requests.exceptions.RequestException("API Error")
        )

        # Act & Assert
        with pytest.raises(requests.exceptions.RequestException):
            usage_service.record_usage(
                user_id=1,
                shop_domain="test.myshopify.com",
                access_token="token",
                subscription_plan=subscription_plan,
                feature_name=feature_name,
                quantity=1,
            )

        assert (
            mock_shopify_client.create_usage_charge.call_count == 3
        )  # 1 initial + 2 retries
        assert "failed, retrying in" in caplog.text
