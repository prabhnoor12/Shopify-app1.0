import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from openai import OpenAI

from my_app.services.analytics_service import MerchantAnalyticsService
from my_app.services.shop_service import ShopifyService
from my_app.models.shop import ShopifyUser
from my_app.models.product import Product
from my_app.models.ab_test import ABTest
from my_app.models.variant import Variant
from my_app.models.user import User

# Mock data
MOCK_SHOPIFY_USER = ShopifyUser(
    id=1,
    user_id=1,
    shop_domain="test.myshopify.com",
    access_token="dummy_token",
    domain="test.myshopify.com",
)
MOCK_PRODUCT = Product(id=101, title="Test Product", shop_id=MOCK_SHOPIFY_USER.id)
MOCK_TEAM_ID = 5


@pytest.fixture
def mock_db_session():
    """Fixture for a mocked database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def mock_shopify_service():
    """Fixture for a mocked Shopify service."""
    return MagicMock(spec=ShopifyService)


@pytest.fixture
def mock_openai_client():
    """Fixture for a mocked OpenAI client."""
    return MagicMock(spec=OpenAI)


@pytest.fixture
def analytics_service(mock_db_session, mock_shopify_service, mock_openai_client):
    """Fixture for the MerchantAnalyticsService."""
    return MerchantAnalyticsService(
        db=mock_db_session,
        shopify_service=mock_shopify_service,
        openai_client=mock_openai_client,
    )


def test_get_revenue_attribution(
    analytics_service: MerchantAnalyticsService, mock_shopify_service: MagicMock
):
    """Test revenue attribution calculation."""
    mock_orders = [
        {
            "total_price": "100.00",
            "subtotal_price": "90.00",
            "total_tax": "10.00",
            "total_discounts": "0.00",
        },
        {
            "total_price": "50.00",
            "subtotal_price": "45.00",
            "total_tax": "5.00",
            "total_discounts": "0.00",
        },
    ]
    mock_shopify_service.fetch_orders_for_product.return_value = mock_orders

    result = analytics_service.get_revenue_attribution(
        MOCK_SHOPIFY_USER, MOCK_PRODUCT.id
    )

    assert result["total_revenue"] == 150.00
    assert result["total_orders"] == 2
    assert result["average_order_value"] == 75.00
    mock_shopify_service.fetch_orders_for_product.assert_called_once_with(
        MOCK_SHOPIFY_USER, MOCK_PRODUCT.id
    )


def test_get_revenue_attribution_no_orders(
    analytics_service: MerchantAnalyticsService, mock_shopify_service: MagicMock
):
    """Test revenue attribution with no orders."""
    mock_shopify_service.fetch_orders_for_product.return_value = []

    result = analytics_service.get_revenue_attribution(
        MOCK_SHOPIFY_USER, MOCK_PRODUCT.id
    )

    assert result["total_revenue"] == 0.0
    assert result["total_orders"] == 0
    assert result["average_order_value"] == 0.0


def test_get_description_performance(
    analytics_service: MerchantAnalyticsService, mock_db_session: MagicMock
):
    """Test A/B test description performance analysis."""
    mock_ab_test = ABTest(
        id=1, product_id=MOCK_PRODUCT.id, user_id=MOCK_SHOPIFY_USER.id
    )
    mock_variants = [
        Variant(
            id=1, ab_test_id=1, description="Baseline", impressions=1000, conversions=50
        ),
        Variant(
            id=2,
            ab_test_id=1,
            description="New Version",
            impressions=1000,
            conversions=70,
        ),
    ]
    mock_db_session.query(ABTest).filter.return_value.first.return_value = mock_ab_test
    mock_db_session.query(Variant).filter.return_value.all.return_value = mock_variants

    # Mock revenue data for this product
    analytics_service.get_revenue_attribution = MagicMock(
        return_value={"total_revenue": 1200}
    )

    result = analytics_service.get_description_performance(
        MOCK_SHOPIFY_USER, MOCK_PRODUCT.id
    )

    assert len(result) == 2
    assert result[0]["conversion_rate"] == 5.0
    assert result[1]["conversion_rate"] == 7.0
    assert result[1]["lift_over_baseline"] == 40.00
    assert result[0]["estimated_revenue"] == 500.00
    assert result[1]["estimated_revenue"] == 700.00


def test_get_description_performance_no_ab_test(
    analytics_service: MerchantAnalyticsService, mock_db_session: MagicMock
):
    """Test performance analysis when no A/B test exists."""
    mock_db_session.query(ABTest).filter.return_value.first.return_value = None
    result = analytics_service.get_description_performance(
        MOCK_SHOPIFY_USER, MOCK_PRODUCT.id
    )
    assert result == []


@patch("my_app.services.analytics_service.seo_service")
def test_analyze_seo(mock_seo_service, analytics_service: MerchantAnalyticsService):
    """Test that SEO analysis correctly calls the SEO service."""
    mock_seo_service.analyze_seo.return_value = {"score": 85}
    result = analytics_service.analyze_seo("keyword", "title", "desc")

    mock_seo_service.analyze_seo.assert_called_once_with(
        primary_keyword="keyword",
        title="title",
        description="desc",
        meta_title=None,
        meta_description=None,
    )
    assert result["score"] == 85


@patch("my_app.services.analytics_service.seo_service")
def test_generate_seo_improvement_suggestions(
    mock_seo_service, analytics_service: MerchantAnalyticsService
):
    """Test that SEO suggestions correctly calls the SEO service."""
    analysis = {"score": 60, "issues": ["low keyword density"]}
    mock_seo_service.generate_seo_improvement_suggestions.return_value = (
        "Improve keyword density."
    )

    result = analytics_service.generate_seo_improvement_suggestions(analysis)

    mock_seo_service.generate_seo_improvement_suggestions.assert_called_once_with(
        openai_client=analytics_service.openai_client, analysis_results=analysis
    )
    assert result == "Improve keyword density."


@patch("my_app.services.analytics_service.datetime", wraps=datetime)
def test_get_product_timeline_performance(
    mock_datetime,
    analytics_service: MerchantAnalyticsService,
    mock_db_session: MagicMock,
):
    """Test product timeline performance retrieval."""
    # Use fixed dates to avoid race conditions at midnight
    end_date = datetime(2023, 1, 3).date()
    start_date = datetime(2023, 1, 1).date()

    # Mock datetime.now() to return a fixed date
    mock_datetime.now.return_value = datetime(2023, 1, 3, tzinfo=timezone.utc)

    mock_events = [
        MagicMock(date=start_date, views=10, adds_to_cart=2),
        MagicMock(date=end_date, views=15, adds_to_cart=5),
    ]

    # Make the mock specific to the query being made
    mock_query = mock_db_session.query.return_value
    mock_query.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = mock_events

    result = analytics_service.get_product_timeline_performance(
        MOCK_SHOPIFY_USER, MOCK_PRODUCT.id, days=2
    )

    # Ensure the dates in the result are what we expect
    result_dates = {item["date"] for item in result}
    expected_dates = {
        start_date.isoformat(),
        (start_date + timedelta(days=1)).isoformat(),
        end_date.isoformat(),
    }
    assert result_dates == expected_dates

    # Create a map for easy lookup and assertion
    result_map = {item["date"]: item for item in result}

    assert len(result) == 3
    assert result_map[start_date.isoformat()]["views"] == 10
    assert result_map[(start_date + timedelta(days=1)).isoformat()]["views"] == 0
    assert result_map[end_date.isoformat()]["views"] == 15


def test_get_team_performance(
    analytics_service: MerchantAnalyticsService, mock_db_session: MagicMock
):
    """Test comprehensive team performance metrics."""
    mock_members = [User(id=1, name="Alice"), User(id=2, name="Bob")]
    mock_db_session.query(User).filter.return_value.all.return_value = mock_members

    # Mock different stats queries
    mock_db_session.query.side_effect = [
        # 1. Team members query
        MagicMock(filter=MagicMock(return_value=MagicMock(all=lambda: mock_members))),
        # 2. Audit stats query
        MagicMock(
            filter=MagicMock(
                return_value=MagicMock(
                    group_by=lambda *args: MagicMock(
                        all=lambda: [
                            MagicMock(
                                user_id=1,
                                descriptions_generated=10,
                                descriptions_published=8,
                            ),
                            MagicMock(
                                user_id=2,
                                descriptions_generated=5,
                                descriptions_published=4,
                            ),
                        ]
                    )
                )
            )
        ),
        # 3. Product stats query
        MagicMock(
            join=MagicMock(
                return_value=MagicMock(
                    join=lambda *a, **kw: MagicMock(
                        filter=MagicMock(
                            return_value=MagicMock(
                                group_by=lambda *args: MagicMock(
                                    all=lambda: [
                                        MagicMock(user_id=1, products_managed=2),
                                        MagicMock(user_id=2, products_managed=3),
                                    ]
                                )
                            )
                        )
                    )
                )
            )
        ),
        # 4. Conversion rate stats query
        MagicMock(
            join=MagicMock(
                return_value=MagicMock(
                    join=lambda *a, **kw: MagicMock(
                        join=MagicMock(
                            return_value=MagicMock(
                                join=lambda *a, **kw: MagicMock(
                                    filter=lambda _: MagicMock(
                                        group_by=lambda *args: MagicMock(
                                            all=lambda: [
                                                MagicMock(
                                                    user_id=1,
                                                    total_conversions=100,
                                                    total_impressions=2000,
                                                ),
                                                MagicMock(
                                                    user_id=2,
                                                    total_conversions=120,
                                                    total_impressions=1500,
                                                ),
                                            ]
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
        ),
    ]
    result = analytics_service.get_team_performance(MOCK_TEAM_ID)

    assert len(result) == 2
    assert result[0]["user_name"] == "Alice"
    assert result[0]["descriptions_generated"] == 10
    assert result[0]["products_managed"] == 2
    assert result[0]["average_conversion_rate"] == 5.0
    assert result[1]["user_name"] == "Bob"
    assert result[1]["average_conversion_rate"] == 8.0


def test_check_for_actionable_alerts_high_traffic_no_test(
    analytics_service: MerchantAnalyticsService, mock_db_session: MagicMock
):
    """Test alert for high traffic product with no A/B test."""
    mock_products = [MOCK_PRODUCT]
    mock_db_session.query(Product).filter.return_value.all.return_value = mock_products

    # Mock view counts
    mock_db_session.query().filter().group_by().all.return_value = [
        (str(MOCK_PRODUCT.id), 600)
    ]

    # Mock no performance data (no A/B test)
    analytics_service.get_description_performance = MagicMock(return_value=[])

    alerts = analytics_service.check_for_actionable_alerts(MOCK_SHOPIFY_USER)

    assert len(alerts) == 1
    assert (
        "Opportunity: Product 'Test Product' has high traffic (600 views) but no active A/B test."
        in alerts[0]
    )


def test_check_for_actionable_alerts_underperforming(
    analytics_service: MerchantAnalyticsService, mock_db_session: MagicMock
):
    """Test alert for underperforming variant."""
    mock_products = [MOCK_PRODUCT]
    mock_db_session.query(Product).filter.return_value.all.return_value = mock_products

    performance_data = [{"variant_id": 1, "impressions": 300, "conversion_rate": 0.2}]
    analytics_service.get_description_performance = MagicMock(
        return_value=performance_data
    )

    alerts = analytics_service.check_for_actionable_alerts(MOCK_SHOPIFY_USER)

    assert len(alerts) == 1
    assert (
        "Alert: Description for product 'Test Product' (variant 1) is underperforming"
        in alerts[0]
    )


def test_check_for_actionable_alerts_winner_found(
    analytics_service: MerchantAnalyticsService, mock_db_session: MagicMock
):
    """Test alert for a statistically significant winner."""
    mock_products = [MOCK_PRODUCT]
    mock_db_session.query(Product).filter.return_value.all.return_value = mock_products

    performance_data = [
        {
            "variant_id": 1,
            "impressions": 1000,
            "conversions": 50,
            "conversion_rate": 5.0,
        },
        {
            "variant_id": 2,
            "impressions": 1000,
            "conversions": 100,
            "conversion_rate": 10.0,
        },
    ]
    analytics_service.get_description_performance = MagicMock(
        return_value=performance_data
    )
    analytics_service._is_winner_statistically_significant = MagicMock(
        return_value=True
    )

    alerts = analytics_service.check_for_actionable_alerts(MOCK_SHOPIFY_USER)

    assert len(alerts) == 1
    assert (
        "A/B test for product 'Test Product' has a statistically significant winner!"
        in alerts[0]
    )
    assert "Variant 2 (CR: 10.0%)" in alerts[0]


def test_is_winner_statistically_significant(
    analytics_service: MerchantAnalyticsService,
):
    """Test the statistical significance calculation (Z-test)."""
    # Significant difference
    variant1 = {"impressions": 1000, "conversions": 50}  # 5% CR
    variant2 = {"impressions": 1000, "conversions": 80}  # 8% CR
    assert (
        analytics_service._is_winner_statistically_significant(variant2, variant1)
        is True
    )

    # Insignificant difference
    variant3 = {"impressions": 100, "conversions": 5}  # 5% CR
    variant4 = {"impressions": 100, "conversions": 7}  # 7% CR
    assert (
        analytics_service._is_winner_statistically_significant(variant4, variant3)
        is False
    )

    # No impressions
    variant5 = {"impressions": 0, "conversions": 0}
    variant6 = {"impressions": 100, "conversions": 10}
    assert (
        analytics_service._is_winner_statistically_significant(variant6, variant5)
        is False
    )
