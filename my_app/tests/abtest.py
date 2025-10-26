import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
import json

from my_app.models.ab_test import ABTest, ABTestStatus
from my_app.models.shop import ShopifyUser
from my_app.models.user import User
from my_app.models.variant import Variant
from my_app.models.experiment import (
    Experiment,
    ExperimentStatus,
    ExperimentType,
)
from my_app.models.segment import Segment
from my_app.models.segment_performance import SegmentPerformance
from my_app.services.ab_testing_service import ABTestingService
from my_app.schemas.shop import SaveRequest


def test_create_ab_test(
    ab_testing_service: ABTestingService,
    test_session: Session,
    mock_shopify_user: ShopifyUser,
):
    """Test creating a new A/B test."""
    product_id = "101"
    variants_data = [
        {"description": "New Variant 1", "traffic_allocation": 50},
        {"description": "New Variant 2", "traffic_allocation": 50},
    ]

    ab_test = ab_testing_service.create_ab_test(
        user_id=mock_shopify_user.id,
        product_id=product_id,
        name="Test Name",
        description="Test Description",
        test_type="description",
        variants_data=variants_data,
    )

    assert ab_test is not None
    assert str(ab_test.product_id) == product_id
    assert ab_test.status == ABTestStatus.DRAFT
    assert len(ab_test.variants) == 2
    assert ab_testing_service.audit_log_service.log.called
    assert ab_testing_service.notification_service.create_notification.called

    # Verify it's in the database
    db_test = test_session.get(ABTest, ab_test.id)
    assert db_test is not None
    assert len(db_test.variants) == 2


def test_get_ab_test_by_id(
    ab_testing_service: ABTestingService, created_ab_test: ABTest
):
    """Test retrieving an A/B test by its ID."""
    retrieved_test = ab_testing_service.get_ab_test_by_id(created_ab_test.id)
    assert retrieved_test is not None
    assert retrieved_test.id == created_ab_test.id


def test_update_ab_test_status(
    ab_testing_service: ABTestingService,
    created_ab_test: ABTest,
    mock_shopify_user: ShopifyUser,
):
    """Test updating the status of an A/B test."""
    updated_test = ab_testing_service.update_ab_test_status(
        created_ab_test.id, ABTestStatus.RUNNING, mock_shopify_user.id
    )
    assert updated_test.status == ABTestStatus.RUNNING
    assert ab_testing_service.audit_log_service.log.called


def test_start_test(ab_testing_service: ABTestingService, created_ab_test: ABTest):
    """Test starting an A/B test."""
    started_test = ab_testing_service.start_test(created_ab_test.id)
    assert started_test.status == ABTestStatus.RUNNING


def test_pause_test(ab_testing_service: ABTestingService, created_ab_test: ABTest):
    """Test pausing a running A/B test."""
    ab_testing_service.start_test(created_ab_test.id)
    paused_test = ab_testing_service.pause_test(created_ab_test.id)
    assert paused_test.status == ABTestStatus.PAUSED


def test_end_test(ab_testing_service: ABTestingService, created_ab_test: ABTest):
    """Test ending an A/B test."""
    ab_testing_service.start_test(created_ab_test.id)
    ended_test = ab_testing_service.end_test(created_ab_test.id)
    assert ended_test.status == ABTestStatus.FINISHED


def test_schedule_ab_tests(
    ab_testing_service: ABTestingService,
    test_session: Session,
    mock_shopify_user: ShopifyUser,
):
    """Test scheduling of A/B tests (starting drafts and ending running tests)."""
    now = datetime.now(timezone.utc)
    # Test to be started
    draft_test = ABTest(
        user_id=mock_shopify_user.id,
        product_id="p1",
        name="t",
        description="d",
        test_type="tt",
        status=ABTestStatus.DRAFT,
        start_time=now - timedelta(hours=1),
    )
    # Test to be ended
    running_test = ABTest(
        user_id=mock_shopify_user.id,
        product_id="p2",
        name="t",
        description="d",
        test_type="tt",
        status=ABTestStatus.RUNNING,
        end_time=now - timedelta(hours=1),
    )
    # Test to be ignored
    future_draft = ABTest(
        user_id=mock_shopify_user.id,
        product_id="p3",
        name="t",
        description="d",
        test_type="tt",
        status=ABTestStatus.DRAFT,
        start_time=now + timedelta(hours=1),
    )

    test_session.add_all([draft_test, running_test, future_draft])
    test_session.commit()

    ab_testing_service.schedule_ab_tests()

    test_session.refresh(draft_test)
    test_session.refresh(running_test)
    test_session.refresh(future_draft)

    assert draft_test.status == ABTestStatus.RUNNING
    assert running_test.status == ABTestStatus.FINISHED
    assert future_draft.status == ABTestStatus.DRAFT


@pytest.mark.asyncio
async def test_declare_winner(
    ab_testing_service: ABTestingService,
    created_ab_test: ABTest,
    mock_shopify_user: ShopifyUser,
    test_session: Session,
):
    """Test declaring a winner for an A/B test."""
    winner_variant = created_ab_test.variants[1]
    ab_testing_service.start_test(created_ab_test.id)
    test_session.commit()

    await ab_testing_service.declare_winner(
        created_ab_test.id, winner_variant.id, mock_shopify_user
    )

    concluded_test = ab_testing_service.get_ab_test(created_ab_test.id)
    assert concluded_test.status == ABTestStatus.CONCLUDED
    assert concluded_test.winner_variant_id == winner_variant.id
    assert concluded_test.active_variant_id == winner_variant.id

    # Verify Shopify service was called
    ab_testing_service.shopify_service.save_description.assert_called_once()
    call_args = ab_testing_service.shopify_service.save_description.call_args
    assert call_args.kwargs["user"] == mock_shopify_user
    assert isinstance(call_args.kwargs["request"], SaveRequest)
    assert str(call_args.kwargs["request"].product_id) == created_ab_test.product_id
    assert call_args.kwargs["request"].new_description == winner_variant.description
    assert ab_testing_service.audit_log_service.log.called
    assert ab_testing_service.notification_service.notify_ab_test_completed.called


def test_get_or_create_segment(
    ab_testing_service: ABTestingService, test_session: Session
):
    """Test retrieving an existing segment or creating a new one."""
    # Create new
    segment1 = ab_testing_service.get_or_create_segment("location", "USA")
    assert segment1.id is not None
    assert segment1.type == "location"
    assert segment1.value == "USA"

    # Get existing
    segment2 = ab_testing_service.get_or_create_segment("location", "USA")
    assert segment1.id == segment2.id

    # Test caching
    with patch.object(test_session, "query", wraps=test_session.query) as mock_query:
        ab_testing_service.get_or_create_segment("location", "USA")
        mock_query.assert_not_called()


def test_record_impression_and_conversion_for_segment(
    ab_testing_service: ABTestingService,
    created_experiment: Experiment,
    test_session: Session,
):
    """Test recording impressions and conversions for segments."""
    variant = created_experiment.variants[0]
    context = {"location": "CAN", "referral": "google"}

    # Record impression
    ab_testing_service.record_impression_for_segment(variant.id, context)
    test_session.commit()

    segment_can = ab_testing_service.db.query(Segment).filter_by(value="CAN").one()
    perf_can = (
        ab_testing_service.db.query(SegmentPerformance)
        .filter_by(variant_id=variant.id, segment_id=segment_can.id)
        .one()
    )
    assert perf_can.impressions == 1
    assert perf_can.conversions == 0

    # Record conversion
    ab_testing_service.record_conversion_for_segment(variant.id, context, revenue=50.0)
    test_session.commit()

    ab_testing_service.db.refresh(perf_can)
    segment_google = (
        ab_testing_service.db.query(Segment).filter_by(value="google").one()
    )
    perf_google = (
        ab_testing_service.db.query(SegmentPerformance)
        .filter_by(variant_id=variant.id, segment_id=segment_google.id)
        .one()
    )

    assert perf_can.conversions == 1
    assert perf_can.revenue_data == [50.0]
    assert perf_google.conversions == 1
    assert (
        perf_google.impressions == 1
    )  # Also gets an impression on conversion if it's the first event


def test_get_assigned_variant_for_segment_exploration(
    ab_testing_service: ABTestingService, created_experiment: Experiment
):
    """Test variant assignment for a segment during the exploration (warm-up) phase."""
    context = {"location": "UK"}
    # With no performance data, it should use random assignment
    assigned_variant = ab_testing_service.get_assigned_variant_for_segment(
        created_experiment.id, context, exploration_budget=50
    )
    assert assigned_variant in created_experiment.variants


def test_get_assigned_variant_for_segment_optimization(
    ab_testing_service: ABTestingService,
    created_experiment: Experiment,
    test_session: Session,
):
    """Test variant assignment for a segment during the optimization (Thompson Sampling) phase."""
    context = {"location": "DE"}
    segment = ab_testing_service.get_or_create_segment("location", "DE")
    var1, var2 = created_experiment.variants

    # Create performance data showing var2 is better
    perf1 = SegmentPerformance(
        variant_id=var1.id, segment_id=segment.id, impressions=100, conversions=10
    )
    perf2 = SegmentPerformance(
        variant_id=var2.id, segment_id=segment.id, impressions=100, conversions=20
    )
    test_session.add_all([perf1, perf2])
    test_session.commit()

    # Mock np.random.beta to control the outcome
    with patch("numpy.random.beta") as mock_beta:
        mock_beta.side_effect = [0.1, 0.9]  # Lower sample for var1, higher for var2
        assigned_variant = ab_testing_service.get_assigned_variant_for_segment(
            created_experiment.id, context, exploration_budget=10
        )
        assert assigned_variant.id == var2.id


def test_assign_user_to_variant(
    ab_testing_service: ABTestingService,
    created_experiment: Experiment,
    mock_shopify_user: ShopifyUser,
):
    """Test assigning a user to a variant and stickiness."""
    user_id = mock_shopify_user.id

    # First assignment
    variant1 = ab_testing_service.assign_user_to_variant(created_experiment.id, user_id)
    assert variant1 in created_experiment.variants

    # Second call should return the same variant
    variant2 = ab_testing_service.assign_user_to_variant(created_experiment.id, user_id)
    assert variant1.id == variant2.id


def test_record_impression_click_conversion_and_flush(
    ab_testing_service: ABTestingService, created_ab_test: ABTest, test_session: Session
):
    """Test in-memory metric recording and flushing to the database."""
    variant = created_ab_test.variants[0]
    initial_impressions = variant.impressions
    initial_clicks = variant.clicks
    initial_conversions = variant.conversions

    # Record metrics in memory
    ab_testing_service.record_impression(variant.id)
    ab_testing_service.record_click(variant.id)
    ab_testing_service.record_conversion(
        variant.id, revenue=10.0
    )  # This writes directly, but let's test the others

    # Before flush, DB should be unchanged for impressions and clicks
    test_session.refresh(variant)
    assert variant.impressions == initial_impressions
    assert variant.clicks == initial_clicks

    # Flush metrics
    ab_testing_service.flush_metrics()

    # After flush, DB should be updated
    test_session.refresh(variant)
    assert variant.impressions == initial_impressions + 1
    assert variant.clicks == initial_clicks + 1
    # Note: record_conversion writes through, so it's already updated
    assert variant.conversions == initial_conversions + 1


def test_get_analysis_results(
    ab_testing_service: ABTestingService, created_ab_test: ABTest, test_session: Session
):
    """Test the generation of analysis results for an A/B test."""
    var_a, var_b = created_ab_test.variants
    var_a.impressions = 150
    var_a.conversions = 15
    var_a.continuous_metrics = {"revenue": [10.0] * 15}
    var_b.impressions = 160
    var_b.conversions = 25
    var_b.continuous_metrics = {"revenue": [12.0] * 25}
    test_session.commit()

    results = ab_testing_service.get_analysis_results(
        created_ab_test.id, include_segments=False
    )

    assert len(results["variants"]) == 2
    assert "p_value" in results
    assert "effect_size" in results
    assert "bayesian_probabilities" in results
    assert "t_test_results" in results
    assert results["variants"][0]["id"] == var_a.id
    assert results["variants"][0]["conversion_rate"] == 10.0
    assert results["variants"][0]["total_revenue"] == 150.0
    assert results["variants"][1]["revenue_per_visitor"] > 0


def test_get_winner_significant(
    ab_testing_service: ABTestingService,
    created_ab_test: ABTest,
    test_session: Session,
):
    """Test that a winner is correctly identified when results are significant."""
    variant_a, variant_b = created_ab_test.variants
    variant_a.impressions = 100
    variant_a.conversions = 10
    variant_b.impressions = 100
    variant_b.conversions = 25  # Clearly better
    test_session.commit()

    with patch.object(ab_testing_service, "calculate_conversion_rates") as mock_calc:
        with patch.object(
            ab_testing_service.statistical_service,
            "sequential_probability_ratio_test",
            return_value="accept_h1",
        ):
            winner = ab_testing_service.get_winner(
                created_ab_test.id, min_conversions=5, min_impressions=50
            )
            assert winner is not None
            assert winner.id == variant_b.id


def test_get_winner_no_significance(
    ab_testing_service: ABTestingService,
    created_ab_test: ABTest,
    test_session: Session,
):
    """Test that no winner is returned if not statistically significant."""
    variant_a, variant_b = created_ab_test.variants
    variant_a.impressions = 100
    variant_a.conversions = 10
    variant_b.impressions = 100
    variant_b.conversions = 11
    test_session.commit()

    # Mock the statistical service to return 'continue'
    ab_testing_service.statistical_service.sequential_probability_ratio_test.return_value = "continue"

    winner = ab_testing_service.get_winner(created_ab_test.id)
    assert winner is None


def test_get_winner_insufficient_data(
    ab_testing_service: ABTestingService,
    created_ab_test: ABTest,
    test_session: Session,
):
    """Test that no winner is returned if data is insufficient."""
    variant_a, variant_b = created_ab_test.variants
    variant_a.impressions = 10
    variant_a.conversions = 1
    variant_b.impressions = 10
    variant_b.conversions = 2
    test_session.commit()

    winner = ab_testing_service.get_winner(
        created_ab_test.id, min_impressions=20, min_conversions=5
    )
    assert winner is None


@pytest.mark.asyncio
async def test_check_and_declare_winner(
    ab_testing_service: ABTestingService,
    created_ab_test: ABTest,
    mock_shopify_user: ShopifyUser,
    test_session: Session,
):
    """Test the wrapper function for checking and declaring a winner."""
    variant_a, variant_b = created_ab_test.variants
    variant_a.impressions = 100
    variant_a.conversions = 10
    variant_b.impressions = 100
    variant_b.conversions = 25
    created_ab_test.status = ABTestStatus.RUNNING
    test_session.commit()

    with patch.object(ab_testing_service, "get_winner", return_value=variant_b):
        await ab_testing_service.check_and_declare_winner(created_ab_test.id)

    test_session.refresh(created_ab_test)
    assert created_ab_test.status == ABTestStatus.CONCLUDED
    assert created_ab_test.winner_variant_id == variant_b.id
    ab_testing_service.shopify_service.save_description.assert_called_once()


def test_rotate_and_update_shopify(
    ab_testing_service: ABTestingService,
    created_ab_test: ABTest,
    mock_shopify_user: ShopifyUser,
    test_session: Session,
):
    """Test rotating the active variant and updating Shopify."""
    ab_testing_service.start_test(created_ab_test.id)
    initial_variant = created_ab_test.variants[0]
    created_ab_test.active_variant_id = initial_variant.id
    test_session.commit()

    ab_testing_service.rotate_and_update_shopify(created_ab_test.id)

    rotated_test = ab_testing_service.get_ab_test(created_ab_test.id)
    next_variant = created_ab_test.variants[1]
    assert rotated_test.active_variant_id == next_variant.id

    # Verify Shopify service was called with the next variant's description
    ab_testing_service.shopify_service.save_description.assert_called_once_with(
        user=mock_shopify_user,
        request=SaveRequest(
            product_id=rotated_test.product_id,
            new_description=next_variant.description,
        ),
    )


@pytest.mark.asyncio
async def test_auto_optimize_cycle_promotion(
    ab_testing_service: ABTestingService,
    mock_shopify_user: ShopifyUser,
    test_session: Session,
):
    """Test the auto-optimize cycle promoting a winner."""
    test = ABTest(
        user_id=mock_shopify_user.id,
        product_id="p-auto",
        name="t",
        description="d",
        test_type="tt",
        status=ABTestStatus.RUNNING,
        auto_optimize=True,
    )
    var_a = Variant(ab_test=test, description="A", impressions=100, conversions=10)
    var_b = Variant(ab_test=test, description="B", impressions=100, conversions=30)
    test_session.add_all([test, var_a, var_b])
    test_session.commit()

    with patch.object(ab_testing_service, "get_winner", return_value=var_b):
        await ab_testing_service.auto_optimize_cycle()

    test_session.refresh(test)
    assert test.status == ABTestStatus.CONCLUDED
    assert test.winner_variant_id == var_b.id


@pytest.mark.asyncio
async def test_auto_optimize_cycle_new_test(
    ab_testing_service: ABTestingService,
    mock_shopify_user: ShopifyUser,
    test_session: Session,
):
    """Test the auto-optimize cycle starting a new challenger test."""
    concluded_test = ABTest(
        user_id=mock_shopify_user.id,
        product_id="p-auto-2",
        name="t",
        description="d",
        test_type="tt",
        status=ABTestStatus.CONCLUDED,
        auto_optimize=True,
        auto_optimize_cooldown_days=0,  # No cooldown for test
        end_time=datetime.now(timezone.utc) - timedelta(days=1),
    )
    winner_var = Variant(ab_test=concluded_test, description="Winner", is_control=False)
    test_session.add_all([concluded_test, winner_var])
    test_session.flush()
    concluded_test.winner_variant_id = winner_var.id
    test_session.commit()

    # Mock AI response for new variants
    ab_testing_service._openai_client.chat.completions.create.return_value.choices[
        0
    ].message.content = '{"variants": ["New AI Var 1", "New AI Var 2"]}'
    ab_testing_service.shopify_service.get_product_details.return_value = {
        "title": "Test Product",
        "tags": ["tag1", "tag2"],
    }

    await ab_testing_service.auto_optimize_cycle()

    new_test = (
        test_session.query(ABTest)
        .filter(
            ABTest.product_id == "p-auto-2",
            ABTest.status == ABTestStatus.DRAFT,  # create_ab_test creates it as DRAFT
        )
        .one_or_none()
    )

    assert new_test is not None
    assert new_test.auto_optimize is True
    assert len(new_test.variants) == 3  # Champion + 2 challengers
    assert any(v.is_control for v in new_test.variants)


@pytest.mark.asyncio
async def test_generate_test_hypothesis_with_history(
    ab_testing_service: ABTestingService,
    mock_shopify_user: ShopifyUser,
    test_session: Session,
):
    """Test generating a hypothesis from past test data."""
    # Create historical test data
    past_test = ABTest(
        user_id=mock_shopify_user.id,
        product_id="prod-hist",
        name="t",
        description="d",
        test_type="tt",
        status=ABTestStatus.CONCLUDED,
        end_time=datetime.now(timezone.utc) - timedelta(days=10),
    )
    control = Variant(
        ab_test=past_test,
        description="Control Desc",
        is_control=True,
        impressions=100,
        conversions=5,
    )
    winner = Variant(
        ab_test=past_test,
        description="Winner Desc",
        is_control=False,
        impressions=100,
        conversions=10,
    )
    test_session.add_all([past_test, control, winner])
    test_session.flush()
    past_test.winner_variant_id = winner.id
    test_session.commit()

    # Mock AI response
    mock_response = {
        "analysis": "Descriptions with clear benefits win.",
        "hypothesis": "Focusing on benefits will increase CVR.",
        "type": "description",
        "suggested_product_id": "prod-hist",
    }
    ab_testing_service._openai_client.chat.completions.create.return_value.choices[
        0
    ].message.content = json.dumps(mock_response)

    hypothesis = await ab_testing_service.generate_test_hypothesis(mock_shopify_user)

    assert hypothesis["analysis"] == mock_response["analysis"]
    assert hypothesis["suggested_product_id"] == "prod-hist"
    # Check that the prompt sent to the AI contains a summary of the past test
    prompt = ab_testing_service._openai_client.chat.completions.create.call_args.kwargs[
        "messages"
    ][1]["content"]
    assert "Test on Product ID prod-hist" in prompt


@pytest.mark.asyncio
async def test_generate_test_hypothesis_no_history(
    ab_testing_service: ABTestingService, mock_shopify_user: ShopifyUser
):
    """Test generating a hypothesis when no test history exists."""
    # Mock analytics service to return a best-selling product
    ab_testing_service.analytics_service.get_best_selling_product_id.return_value = (
        "best-seller-123"
    )

    hypothesis = await ab_testing_service.generate_test_hypothesis(mock_shopify_user)

    assert "No test history found" in hypothesis["hypothesis"]
    assert hypothesis["suggested_product_id"] == "best-seller-123"


@pytest.mark.asyncio
async def test_create_ai_driven_test(
    ab_testing_service: ABTestingService, mock_shopify_user: ShopifyUser
):
    """Test the end-to-end creation of an AI-driven test."""
    # Mock hypothesis generation
    mock_hypothesis = {
        "analysis": "Analysis",
        "hypothesis": "Hypothesis",
        "type": "description",
        "suggested_product_id": "555",
    }
    ab_testing_service.generate_test_hypothesis = AsyncMock(
        return_value=mock_hypothesis
    )

    # Mock variant generation
    mock_variants = [{"description": "AI Variant 1"}, {"description": "AI Variant 2"}]
    ab_testing_service.ai_recommendations_service.generate_variants.return_value = (
        mock_variants
    )

    # Mock getting the control description
    ab_testing_service.shopify_service.get_product.return_value = {
        "body_html": "Control Description"
    }

    new_test = await ab_testing_service.create_ai_driven_test(mock_shopify_user)

    assert new_test is not None
    assert new_test.product_id == "555"
    assert new_test.status == ABTestStatus.RUNNING  # Should be started automatically
    assert len(new_test.variants) == 3  # Control + 2 AI variants
    assert ab_testing_service.generate_test_hypothesis.called
    ab_testing_service.ai_recommendations_service.generate_variants.assert_called_once()


def test_get_ab_test(ab_testing_service: ABTestingService, created_ab_test: ABTest):
    """Test retrieving an A/B test by its ID using the get_ab_test method."""
    retrieved_test = ab_testing_service.get_ab_test(created_ab_test.id)
    assert retrieved_test is not None
    assert retrieved_test.id == created_ab_test.id


def test_get_all_ab_tests(
    ab_testing_service: ABTestingService,
    created_ab_test: ABTest,
    mock_shopify_user: ShopifyUser,
):
    """Test retrieving all A/B tests."""
    # created_ab_test is already one test
    ab_testing_service.create_ab_test(
        user_id=mock_shopify_user.id,
        product_id="p2",
        name="t2",
        description="d2",
        test_type="tt",
        variants_data=[],
    )

    all_tests = ab_testing_service.get_all_ab_tests()
    assert len(all_tests) >= 2


def test_get_ab_tests_by_user_id(
    ab_testing_service: ABTestingService,
    test_session: Session,
    mock_shopify_user: ShopifyUser,
):
    """Test retrieving all A/B tests for a specific user."""
    # Create another user
    regular_user2 = User(
        id=2,
        email="test2@example.com",
        hashed_password="password",
    )
    user2 = ShopifyUser(
        id=2,
        user_id=regular_user2.id,
        shop_domain="test-shop2.myshopify.com",
        access_token="token2",
        domain="test-shop2.myshopify.com",
    )
    test_session.add_all([regular_user2, user2])
    test_session.commit()

    # Create tests for both users
    ab_testing_service.create_ab_test(
        user_id=mock_shopify_user.id,
        product_id="p-user1",
        name="t-user1",
        description="d",
        test_type="tt",
        variants_data=[],
    )
    ab_testing_service.create_ab_test(
        user_id=user2.id,
        product_id="p-user2",
        name="t-user2",
        description="d",
        test_type="tt",
        variants_data=[],
    )

    user1_tests = ab_testing_service.get_ab_tests_by_user_id(mock_shopify_user.id)
    assert len(user1_tests) >= 1
    assert all(t.user_id == mock_shopify_user.id for t in user1_tests)

    user2_tests = ab_testing_service.get_ab_tests_by_user_id(user2.id)
    assert len(user2_tests) == 1
    assert user2_tests[0].user_id == user2.id


def test_delete_ab_test(
    ab_testing_service: ABTestingService,
    created_ab_test: ABTest,
    test_session: Session,
    mock_shopify_user: ShopifyUser,
):
    """Test deleting an A/B test."""
    test_id = created_ab_test.id
    user_id = mock_shopify_user.id

    ab_testing_service.delete_ab_test(test_id, user_id)

    deleted_test = ab_testing_service.get_ab_test_by_id(test_id)
    assert deleted_test is None


def test_get_variant_by_id(
    ab_testing_service: ABTestingService, created_ab_test: ABTest
):
    """Test retrieving a variant by its ID."""
    variant_to_find = created_ab_test.variants[0]

    retrieved_variant = ab_testing_service.get_variant_by_id(variant_to_find.id)

    assert retrieved_variant is not None
    assert retrieved_variant.id == variant_to_find.id
    assert retrieved_variant.description == variant_to_find.description
