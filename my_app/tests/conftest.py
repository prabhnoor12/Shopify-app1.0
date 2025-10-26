import pytest
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timezone, timedelta
import json

from my_app.database import Base
from my_app.models.ab_test import ABTest, ABTestStatus
from my_app.models.shop import ShopifyUser
from my_app.models.user import User
from my_app.models.variant import Variant
from my_app.models.experiment import (
    Experiment,
    ExperimentStatus,
    ExperimentType,
)
from my_app.models.scheduled_ab_test_rotation import ScheduledABTestRotation
from my_app.models.segment import Segment
from my_app.models.segment_performance import SegmentPerformance
from my_app.services.ab_testing_service import ABTestingService
from my_app.schemas.shop import SaveRequest
from my_app.models.agency import Agency
from my_app.models.role_version import RoleVersion
# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine():
    """Create an in-memory SQLite engine for tests."""
    engine = create_engine(
        TEST_DATABASE_URL, echo=False, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def test_session(test_engine):
    """Create a new database session for a test."""
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = session_factory()
    yield session
    session.rollback()
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
    session.close()


@pytest.fixture
def mock_openai_client():
    """Fixture for a mocked OpenAI client."""
    mock = MagicMock()
    # Mock the async chat completions create method
    mock.chat.completions.create = AsyncMock()
    return mock


@pytest.fixture
def mock_audit_log_service():
    """Fixture for a mocked AuditLogService."""
    return MagicMock()


@pytest.fixture
def mock_notification_service():
    """Fixture for a mocked NotificationService."""
    return MagicMock()


@pytest.fixture
def mock_ai_recommendations_service():
    """Fixture for a mocked AIRecommendationsService."""
    return MagicMock()


@pytest.fixture
def mock_http_client():
    """Fixture for a mocked HTTP client."""
    return MagicMock()


@pytest.fixture
def mock_seo_service():
    """Fixture for a mocked SEOService."""
    return MagicMock()


@pytest.fixture
def ab_testing_service(
    test_session: Session,  # Use the test_session fixture
    mock_openai_client: MagicMock,
    mock_audit_log_service: MagicMock,
    mock_notification_service: MagicMock,
    mock_ai_recommendations_service: MagicMock,
    mock_http_client: MagicMock,
    mock_seo_service: MagicMock,
):
    """Create an instance of the ABTestingService for tests."""
    service = ABTestingService(
        db=test_session,  # Use the session from the fixture
        openai_client=mock_openai_client,
        audit_log_service=mock_audit_log_service,
        notification_service=mock_notification_service,
        ai_recommendations_service=mock_ai_recommendations_service,
        http_client=mock_http_client,
        seo_service=mock_seo_service,
    )
    # Mock the ShopifyService and other services within the ABTestingService
    service.shopify_service = MagicMock()
    service.shopify_service.save_description = AsyncMock()
    service.shopify_service.get_product_details = AsyncMock(
        return_value={"title": "Test Product", "tags": ["tag1", "tag2"]}
    )
    service.analytics_service = MagicMock()
    service.statistical_service = MagicMock()
    service.statistical_service.calculate_proportions_z_test.return_value = 0.04
    service.statistical_service.calculate_effect_size_cohen_h.return_value = 0.2
    service.statistical_service.calculate_confidence_interval.return_value = (
        0.08,
        0.12,
    )
    service.statistical_service.bayesian_probability_b_beats_a.return_value = 0.95
    service.statistical_service.calculate_t_test.return_value = 0.03
    service.statistical_service.sequential_probability_ratio_test.return_value = (
        "accept_h1"
    )

    yield service


@pytest.fixture
def mock_shopify_user(test_session: Session) -> ShopifyUser:
    """Fixture for a mocked ShopifyUser."""
    # Create a regular user first
    regular_user = User(
        id=1,
        email="test@example.com",
        hashed_password="password",
    )
    test_session.add(regular_user)
    test_session.flush()

    user = ShopifyUser(
        id=1,
        user_id=regular_user.id,
        shop_domain="test-shop.myshopify.com",
        access_token="test_access_token",
        domain="test-shop.myshopify.com",
    )
    test_session.add(user)
    test_session.commit()
    return user


@pytest.fixture
def created_ab_test(
    ab_testing_service: ABTestingService,
    mock_shopify_user: ShopifyUser,
    test_session: Session,
) -> ABTest:
    """Fixture to create a sample A/B test."""
    variants_data = [
        {"description": "Variant A", "traffic_allocation": 50, "is_control": True},
        {"description": "Variant B", "traffic_allocation": 50, "is_control": False},
    ]
    test = ab_testing_service.create_ab_test(
        user_id=mock_shopify_user.id,
        product_id="101",
        name="Test Name",
        description="Test Description",
        test_type="description",
        variants_data=variants_data,
    )
    test_session.commit()
    return test


@pytest.fixture
def created_experiment(
    test_session: Session, mock_shopify_user: ShopifyUser
) -> Experiment:
    """Fixture for a created experiment with variants."""
    exp = Experiment(
        name="Test Experiment",
        status=ExperimentStatus.RUNNING,
        type=ExperimentType.AB_TEST,
    )
    test_session.add(exp)
    test_session.flush()

    var1 = Variant(experiment_id=exp.id, description="Exp Var 1", traffic_allocation=50)
    var2 = Variant(experiment_id=exp.id, description="Exp Var 2", traffic_allocation=50)
    test_session.add_all([var1, var2])
    test_session.commit()
    test_session.refresh(exp)
    return exp
