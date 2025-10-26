import logging
import asyncio
import random
import numpy as np
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from ..models.ab_test import ABTest, ABTestStatus
from ..models.segment import Segment
from ..models.segment_performance import SegmentPerformance
from ..models.variant import Variant
from ..models.shop import ShopifyUser
from ..models.experiment import (
    Experiment,
    UserVariantAssignment,
    ExperimentType,
    ExperimentStatus,
)
from ..services.shop_service import ShopifyService
from ..services.statistical_service import StatisticalService
from ..services.analytics_service import MerchantAnalyticsService
from ..services.ai_recommendations_service import AIRecommendationsService
from ..services.audit_service import AuditLogService as AuditService
from ..services.notification_service import NotificationService
from ..dependencies.config import settings
import json
from sqlalchemy.orm.attributes import flag_modified


from ..schemas.shop import SaveRequest
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)


class ABTestingService:
    def __init__(
        self,
        db: Session,
        openai_client: OpenAI,
        audit_log_service: AuditService,
        notification_service: NotificationService,
        ai_recommendations_service: AIRecommendationsService,
        http_client,
        seo_service,
    ):
        self.db = db
        self.shopify_service = ShopifyService(db, openai_client, http_client)
        self.analytics_service = MerchantAnalyticsService(
            db, self.shopify_service, openai_client, seo_service
        )
        self.statistical_service = StatisticalService(db)
        self.audit_log_service = audit_log_service
        self.notification_service = notification_service
        self.ai_recommendations_service = ai_recommendations_service
        self._impressions = defaultdict(int)
        self._clicks = defaultdict(int)
        self._conversions = defaultdict(int)
        self._openai_client = openai_client

    # --- Personalized A/B Testing (Segmentation) ---

    def get_or_create_segment(self, segment_type: str, segment_value: str) -> Segment:
        """
        Retrieves an existing segment or creates a new one.
        Caches results in memory for the lifetime of the request to reduce DB queries.
        """
        if not hasattr(self, "_segment_cache"):
            self._segment_cache = {}

        cache_key = (segment_type, segment_value)
        if cache_key in self._segment_cache:
            return self._segment_cache[cache_key]

        segment = (
            self.db.query(Segment)
            .filter_by(type=segment_type, value=segment_value)
            .first()
        )
        if not segment:
            segment = Segment(type=segment_type, value=segment_value)
            self.db.add(segment)
            self.db.flush()
            self.db.refresh(segment)

        self._segment_cache[cache_key] = segment
        return segment

    def get_assigned_variant_for_segment(
        self,
        experiment_id: int,
        visitor_context: Dict[str, Any],
        exploration_budget: int = 50,
    ) -> Variant:
        """
        Assigns a variant to a visitor based on their segment using Thompson Sampling.
        This is the core of personalized A/B testing.
        """
        experiment = (
            self.db.query(Experiment)
            .options(selectinload(Experiment.variants))
            .get(experiment_id)
        )
        if not experiment or not experiment.variants:
            raise FileNotFoundError(
                f"Experiment with ID {experiment_id} not found or has no variants."
            )

        # For now, we'll prioritize one segment type. A more complex system could combine them.
        segment_type = "referral" if "referral" in visitor_context else "location"
        segment_value = visitor_context.get(segment_type, "default")

        segment = self.get_or_create_segment(segment_type, segment_value)

        variants = experiment.variants

        # --- Warm-up Phase (Exploration) for this specific segment ---
        total_segment_impressions = sum(
            self.db.query(SegmentPerformance.impressions)
            .filter_by(variant_id=v.id, segment_id=segment.id)
            .scalar()
            or 0
            for v in variants
        )

        if total_segment_impressions < exploration_budget:
            # Fallback to random assignment during the warm-up phase for this segment
            traffic_allocations = [v.traffic_allocation for v in variants]
            if sum(traffic_allocations) == 0:
                traffic_allocations = [1] * len(variants)
            return random.choices(variants, weights=traffic_allocations, k=1)[0]

        # --- Optimization Phase (Thompson Sampling for the segment) ---
        best_variant = None
        max_sample = -1
        for variant in variants:
            perf = (
                self.db.query(SegmentPerformance)
                .filter_by(variant_id=variant.id, segment_id=segment.id)
                .first()
            )

            impressions = perf.impressions if perf and perf.impressions > 0 else 1
            conversions = perf.conversions if perf else 0
            conversions = min(conversions, impressions)

            alpha = 1 + conversions
            beta = 1 + (impressions - conversions)

            sample = np.random.beta(alpha, beta)
            if sample > max_sample:
                max_sample = sample
                best_variant = variant

        return best_variant if best_variant else random.choice(variants)

    def record_impression_for_segment(
        self, variant_id: int, visitor_context: Dict[str, Any]
    ):
        """
        Records an impression for a variant across multiple visitor segments efficiently.
        All database operations are handled in a single transaction.
        """
        # The try-except block with rollback was causing issues with nested transactions.
        # The `begin_nested` context manager is sufficient to handle rollbacks for this unit of work.
        with self.db.begin_nested():
            for segment_type, segment_value in visitor_context.items():
                if not segment_value:
                    continue
                segment = self.get_or_create_segment(segment_type, segment_value)

                perf = (
                    self.db.query(SegmentPerformance)
                    .filter_by(variant_id=variant_id, segment_id=segment.id)
                    .with_for_update()
                    .first()
                )

                if perf:
                    perf.impressions += 1
                else:
                    perf = SegmentPerformance(
                        variant_id=variant_id, segment_id=segment.id, impressions=1
                    )
                    self.db.add(perf)

    def record_conversion_for_segment(
        self, variant_id: int, visitor_context: Dict[str, Any], revenue: float = 0.0
    ):
        """
        Records a conversion for a variant across multiple visitor segments efficiently.
        All database operations are handled in a single transaction.
        """
        with self.db.begin_nested():
            for segment_type, segment_value in visitor_context.items():
                if not segment_value:
                    continue
                segment = self.get_or_create_segment(segment_type, segment_value)

                perf = (
                    self.db.query(SegmentPerformance)
                    .filter_by(variant_id=variant_id, segment_id=segment.id)
                    .with_for_update()
                    .first()
                )

                if perf:
                    perf.conversions += 1
                    if perf.revenue_data is None:
                        perf.revenue_data = []
                    perf.revenue_data.append(revenue)
                    flag_modified(perf, "revenue_data")
                else:
                    perf = SegmentPerformance(
                        variant_id=variant_id,
                        segment_id=segment.id,
                        impressions=1,
                        conversions=1,
                        revenue_data=[revenue],
                    )
                    self.db.add(perf)  # --- End of Segmentation ---

    def get_ab_test_by_id(self, ab_test_id: int) -> ABTest | None:
        """
        Retrieves an A/B test by its ID using a direct lookup.
        """
        return self.db.get(ABTest, ab_test_id)

    def get_running_auto_promote_tests(self) -> list[ABTest]:
        """
        Retrieves all running A/B tests with auto-promotion enabled.
        """
        return (
            self.db.query(ABTest)
            .filter(
                ABTest.status == ABTestStatus.RUNNING,
                ABTest.auto_promote_winner == True,
            )
            .all()
        )

    async def declare_winner(self, ab_test_id: int, variant_id: int, user: ShopifyUser):
        """
        Declares a winner, updates the product description, and concludes the test.
        This operation is now fully asynchronous.
        """
        try:
            with self.db.begin_nested():
                ab_test = self.db.get(ABTest, ab_test_id)
                if not ab_test:
                    raise FileNotFoundError(f"A/B test with ID {ab_test_id} not found.")

                winner_variant = self.db.get(Variant, variant_id)
                if not winner_variant or winner_variant.ab_test_id != ab_test_id:
                    raise ValueError(
                        f"Winning variant {variant_id} not found or does not belong to test {ab_test_id}."
                    )

                original_status = ab_test.status
                ab_test.status = ABTestStatus.CONCLUDED
                ab_test.winner_variant_id = winner_variant.id
                ab_test.active_variant_id = winner_variant.id
                ab_test.end_time = datetime.now(timezone.utc)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error declaring winner, rolling back: {e}")
            raise

        try:
            # Asynchronously update the product on Shopify
            await self.shopify_service.save_description(
                user=user,
                request=SaveRequest(
                    product_id=ab_test.product_id,
                    new_description=winner_variant.description,
                ),
            )
        except Exception as e:
            logger.error(
                f"Failed to update Shopify description for test {ab_test_id}: {e}"
            )
            # Optionally, re-queue this task or notify admins
            # For now, we proceed without rolling back the DB change

        self.audit_log_service.log(
            user_id=user.id,
            action="promote_ab_test_winner",
            target_entity="ab_test",
            target_id=ab_test_id,
            change_details={
                "before": {"status": original_status.value},
                "after": {
                    "status": ABTestStatus.CONCLUDED.value,
                    "winner_variant_id": variant_id,
                },
            },
        )

        self.notification_service.notify_ab_test_completed(
            user.id, ab_test_id, variant_id
        )

        logger.info(
            f"A/B test {ab_test_id} concluded. Variant {variant_id} declared and promoted as winner."
        )

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
    def assign_user_to_variant(self, experiment_id: int, user_id: int) -> Variant:
        try:
            with self.db.begin_nested():
                assignment = (
                    self.db.query(UserVariantAssignment)
                    .filter_by(user_id=user_id, experiment_id=experiment_id)
                    .with_for_update()
                    .first()
                )
                if assignment:
                    return self.db.query(Variant).get(assignment.variant_id)

                experiment = (
                    self.db.query(Experiment)
                    .options(selectinload(Experiment.variants))
                    .get(experiment_id)
                )
                if not experiment or not experiment.variants:
                    raise ValueError("Experiment not found or has no variants")

                variants = experiment.variants
                traffic_allocations = [v.traffic_allocation for v in variants]
                chosen_variant = random.choices(
                    variants, weights=traffic_allocations, k=1
                )[0]

                new_assignment = UserVariantAssignment(
                    user_id=user_id,
                    experiment_id=experiment_id,
                    variant_id=chosen_variant.id,
                )
                self.db.add(new_assignment)
                return chosen_variant
        except IntegrityError:
            self.db.rollback()
            logger.warning(
                f"Race condition detected for user {user_id} in experiment {experiment_id}. Retrying."
            )
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error assigning user to variant: {e}")
            raise

    def get_assigned_variant(
        self,
        experiment_id: int,
        user_id: int,
        visitor_context: Dict[str, Any] | None = None,
    ) -> Variant:
        experiment = self.db.query(Experiment).get(experiment_id)
        if not experiment:
            raise ValueError("Experiment not found")

        # If context is provided and it's a personalized test, use the segmentation logic
        if visitor_context and experiment.type in [
            ExperimentType.MAB_TEST,
            ExperimentType.AB_TEST,
        ]:
            return self.get_assigned_variant_for_segment(experiment_id, visitor_context)

        # Fallback to general assignment logic
        if experiment.type == ExperimentType.MAB_TEST:
            return self.assign_variant_thompson_sampling(experiment_id, user_id)

        assignment = (
            self.db.query(UserVariantAssignment)
            .filter_by(user_id=user_id, experiment_id=experiment_id)
            .first()
        )
        if not assignment:
            return self.assign_user_to_variant(experiment_id, user_id)
        return self.db.query(Variant).get(assignment.variant_id)

    def assign_variant_thompson_sampling(
        self, experiment_id: int, user_id: int, exploration_budget: int = 100
    ) -> Variant:
        """
        Assigns a variant using a Thompson Sampling multi-arm bandit algorithm
        with a warm-up phase (exploration budget).
        """
        experiment = (
            self.db.query(Experiment)
            .options(selectinload(Experiment.variants))
            .get(experiment_id)
        )
        if not experiment or not experiment.variants:
            raise ValueError("Experiment not found or has no variants")

        variants = experiment.variants
        total_impressions = sum(v.impressions for v in variants)

        if total_impressions < exploration_budget:
            traffic_allocations = [v.traffic_allocation for v in variants]
            if sum(traffic_allocations) == 0:
                traffic_allocations = [1] * len(variants)
            return random.choices(variants, weights=traffic_allocations, k=1)[0]

        best_variant = None
        max_sample = -1
        for variant in variants:
            impressions = variant.impressions if variant.impressions > 0 else 1
            conversions = min(variant.conversions, impressions)
            alpha = 1 + conversions
            beta = 1 + (impressions - conversions)
            sample = np.random.beta(alpha, beta)
            if sample > max_sample:
                max_sample = sample
                best_variant = variant

        return best_variant if best_variant else random.choice(variants)

    def get_running_experiments(self) -> list[Experiment]:
        return (
            self.db.query(Experiment)
            .filter(Experiment.status == ExperimentStatus.RUNNING)
            .all()
        )

    def create_ab_test(
        self,
        user_id: int,
        product_id: str,
        name: str,
        description: str,
        test_type: str,
        variants_data: list[dict],
        start_time: datetime = None,
        end_time: datetime = None,
        auto_optimize: bool = False,
        auto_optimize_cooldown_days: int = 7,
        db: Session = None,
    ) -> ABTest:
        db_session = db or self.db
        new_test = ABTest(
            user_id=user_id,
            product_id=product_id,
            name=name,
            description=description,
            test_type=test_type,
            status=ABTestStatus.DRAFT,
            start_time=start_time,
            end_time=end_time,
            auto_optimize=auto_optimize,
            auto_optimize_cooldown_days=auto_optimize_cooldown_days,
            goal_metric="revenue_per_visitor",
        )
        db_session.add(new_test)
        db_session.flush()

        for variant_data in variants_data:
            db_session.add(Variant(ab_test_id=new_test.id, **variant_data))

        db_session.commit()
        self.audit_log_service.log(
            user_id=user_id,
            action="create_ab_test",
            target_entity="ab_test",
            target_id=new_test.id,
            change_details={
                "product_id": product_id,
                "status": "DRAFT",
                "auto_optimize": auto_optimize,
            },
        )
        self.notification_service.create_notification(
            user_id=user_id,
            event_type="ab_test_created",
            data={"test_id": new_test.id, "product_id": product_id},
        )
        return new_test

    def update_ab_test_status(
        self, test_id: int, status: ABTestStatus, user_id: int, db: Session = None
    ) -> ABTest:
        db_session = db or self.db
        ab_test = db_session.get(ABTest, test_id)
        if not ab_test:
            raise ValueError("A/B test not found")
        original_status = ab_test.status
        ab_test.status = status
        db_session.commit()
        db_session.refresh(ab_test)
        self.audit_log_service.log(
            user_id=user_id,
            action="update_ab_test_status",
            target_entity="ab_test",
            target_id=test_id,
            change_details={
                "before": {"status": original_status.value},
                "after": {"status": status.value},
            },
        )
        return ab_test

    def get_ab_tests_by_user_id(self, user_id: int) -> list[ABTest]:
        """
        Retrieves all A/B tests for a specific user.
        """
        return self.db.query(ABTest).filter(ABTest.user_id == user_id).all()

    def get_all_ab_tests(self) -> list[ABTest]:
        """
        Retrieves all A/B tests from the database.
        """
        return self.db.query(ABTest).all()

    def delete_ab_test(self, ab_test_id: int, user_id: int):
        """
        Deletes an A/B test and its associated variants.
        """
        ab_test = self.get_ab_test_by_id(ab_test_id)
        if ab_test:
            # Log the deletion before committing
            self.audit_log_service.log(
                user_id=user_id,
                action="delete_ab_test",
                target_entity="ab_test",
                target_id=ab_test_id,
                change_details={"product_id": ab_test.product_id, "name": ab_test.name},
            )
            self.db.delete(ab_test)
            self.db.commit()
            logger.info(f"A/B test {ab_test_id} has been deleted by user {user_id}.")
        else:
            logger.warning(f"Attempted to delete non-existent A/B test {ab_test_id}")

    def get_variant_by_id(self, variant_id: int) -> Variant | None:
        """
        Retrieves a variant by its ID.
        """
        return self.db.get(Variant, variant_id)

    def get_ab_test(self, ab_test_id: int) -> ABTest:
        return self.get_ab_test_by_id(ab_test_id)

    def schedule_ab_tests(self):
        now = datetime.now(timezone.utc)
        draft_tests = (
            self.db.execute(
                select(ABTest).filter(
                    ABTest.status == ABTestStatus.DRAFT, ABTest.start_time <= now
                )
            )
            .scalars()
            .all()
        )
        for test in draft_tests:
            self.start_test(test.id)
        running_tests = (
            self.db.execute(
                select(ABTest).filter(
                    ABTest.status == ABTestStatus.RUNNING, ABTest.end_time <= now
                )
            )
            .scalars()
            .all()
        )
        for test in running_tests:
            self.end_test(test.id)

    def start_test(self, ab_test_id: int) -> ABTest:
        ab_test = self.get_ab_test_by_id(ab_test_id)
        if not ab_test:
            raise ValueError("A/B test not found")
        ab_test.status = ABTestStatus.RUNNING
        self.db.commit()
        logger.info("A/B test %d started.", ab_test_id)
        return ab_test

    def pause_test(self, ab_test_id: int) -> ABTest:
        ab_test = self.get_ab_test_by_id(ab_test_id)
        if not ab_test:
            raise ValueError("A/B test not found")
        if ab_test.status != ABTestStatus.RUNNING:
            raise ValueError("A/B test is not running")
        ab_test.status = ABTestStatus.PAUSED
        self.db.commit()
        logger.info("A/B test %d paused.", ab_test_id)
        return ab_test

    def end_test(self, ab_test_id: int) -> ABTest:
        ab_test = self.get_ab_test_by_id(ab_test_id)
        if not ab_test:
            raise ValueError("A/B test not found")
        ab_test.status = ABTestStatus.FINISHED
        self.db.commit()
        logger.info("A/B test %d finished.", ab_test_id)
        return ab_test

    def record_impression(
        self, variant_id: int, visitor_context: Dict[str, Any] | None = None
    ):
        self._impressions[variant_id] += 1
        if visitor_context:
            try:
                self.record_impression_for_segment(variant_id, visitor_context)
            except Exception as e:
                logger.error(
                    f"Error in segmented impression recording for variant {variant_id}: {e}"
                )

    def record_click(self, variant_id: int):
        self._clicks[variant_id] += 1

    def record_conversion(
        self,
        variant_id: int,
        revenue: float = 0.0,
        visitor_context: Dict[str, Any] | None = None,
    ):
        try:
            with self.db.begin_nested():
                variant = (
                    self.db.query(Variant)
                    .filter(Variant.id == variant_id)
                    .with_for_update()
                    .first()
                )
                if not variant:
                    logger.warning(
                        f"Attempted to record conversion for non-existent variant {variant_id}"
                    )
                    return
                if variant.continuous_metrics is None:
                    variant.continuous_metrics = {"revenue": []}
                elif "revenue" not in variant.continuous_metrics:
                    variant.continuous_metrics["revenue"] = []
                variant.continuous_metrics["revenue"].append(revenue)
                flag_modified(variant, "continuous_metrics")
                variant.conversions = Variant.conversions + 1
        except Exception as e:
            self.db.rollback()
            logger.error(
                f"Error in global conversion recording for variant {variant_id}: {e}"
            )
            raise
        if visitor_context:
            try:
                self.record_conversion_for_segment(variant_id, visitor_context, revenue)
            except Exception as e:
                logger.error(
                    f"Error in segmented conversion recording for variant {variant_id}: {e}"
                )

    def flush_metrics(self):
        logger.info("Flushing metrics to database.")
        try:
            with self.db.begin_nested():
                if self._impressions:
                    for variant_id, count in self._impressions.items():
                        self.db.query(Variant).filter(Variant.id == variant_id).update(
                            {"impressions": Variant.impressions + count},
                            synchronize_session=False,
                        )
                if self._clicks:
                    for variant_id, count in self._clicks.items():
                        self.db.query(Variant).filter(Variant.id == variant_id).update(
                            {"clicks": Variant.clicks + count},
                            synchronize_session=False,
                        )
            self.db.commit()
        except Exception as e:
            logger.error(f"Error flushing metrics, rolling back: {e}")
            self.db.rollback()
        finally:
            self._impressions.clear()
            self._clicks.clear()
            self._conversions.clear()
            logger.info("Metrics flushed successfully.")

    def calculate_conversion_rates(self, ab_test_id: int):
        ab_test = self.get_ab_test_by_id(ab_test_id)
        if ab_test:
            for variant in ab_test.variants:
                if (
                    variant.continuous_metrics
                    and "revenue" in variant.continuous_metrics
                ):
                    variant.conversions = len(variant.continuous_metrics["revenue"])
                # If conversions are not derived from revenue, they might be set directly.
                # We calculate conversion_rate based on existing conversions and impressions.
                if variant.impressions > 0:
                    variant.conversion_rate = (
                        (variant.conversions or 0) / variant.impressions
                    ) * 100
                else:
                    variant.conversion_rate = 0.0
            self.db.commit()

    def _calculate_statistical_significance(
        self, variant_a: Variant, variant_b: Variant
    ) -> tuple[float, float, tuple[float, float], tuple[float, float]]:
        p_value = self.statistical_service.calculate_proportions_z_test(
            variant_a.conversions,
            variant_a.impressions,
            variant_b.conversions,
            variant_b.impressions,
        )
        effect_size = self.statistical_service.calculate_effect_size_cohen_h(
            variant_a.conversions,
            variant_a.impressions,
            variant_b.conversions,
            variant_b.impressions,
        )
        ci_a = self.statistical_service.calculate_confidence_interval(
            variant_a.conversions, variant_a.impressions
        )
        ci_b = self.statistical_service.calculate_confidence_interval(
            variant_b.conversions, variant_b.impressions
        )
        return p_value, effect_size, ci_a, ci_b

    def record_continuous_metric(self, variant_id: int, metric_name: str, value: float):
        variant = self.db.get(Variant, variant_id)
        if not variant:
            raise ValueError("Variant not found")
        if variant.continuous_metrics is None:
            variant.continuous_metrics = {}
        if metric_name not in variant.continuous_metrics:
            variant.continuous_metrics[metric_name] = []
        variant.continuous_metrics[metric_name].append(value)
        flag_modified(variant, "continuous_metrics")
        self.db.commit()

    def get_analysis_results(
        self, ab_test_id: int, include_segments: bool = True
    ) -> dict:
        ab_test = self.get_ab_test_by_id(ab_test_id)
        if not ab_test:
            raise ValueError("A/B test not found")

        results = {"variants": [], "bayesian_probabilities": {}}
        variants = ab_test.variants

        for variant in variants:
            ci_lower, ci_upper = self.statistical_service.calculate_confidence_interval(
                variant.conversions, variant.impressions
            )
            revenue_data = (
                variant.continuous_metrics.get("revenue", [])
                if variant.continuous_metrics
                else []
            )
            total_revenue = sum(revenue_data)
            aov = total_revenue / len(revenue_data) if revenue_data else 0
            rpv = total_revenue / variant.impressions if variant.impressions > 0 else 0
            variant_result = {
                "id": variant.id,
                "description": variant.description,
                "impressions": variant.impressions,
                "conversions": variant.conversions,
                "conversion_rate": (variant.conversions / variant.impressions) * 100
                if variant.impressions > 0
                else 0,
                "confidence_interval": [ci_lower, ci_upper],
                "total_revenue": total_revenue,
                "average_order_value": aov,
                "revenue_per_visitor": rpv,
            }
            if include_segments:
                variant_result["segments"] = self._get_segment_results_for_variant(
                    variant.id
                )
            results["variants"].append(variant_result)

        if len(variants) >= 2:
            p_values, effect_sizes, t_test_results = [], [], {}
            for i in range(len(variants)):
                for j in range(i + 1, len(variants)):
                    var_a, var_b = variants[i], variants[j]
                    p_val, eff_size, _, _ = self._calculate_statistical_significance(
                        var_a, var_b
                    )
                    p_values.append(p_val)
                    effect_sizes.append(eff_size)
                    results["bayesian_probabilities"][
                        f"{var_b.id}_beats_{var_a.id}"
                    ] = self.statistical_service.bayesian_probability_b_beats_a(
                        var_a.conversions,
                        var_a.impressions,
                        var_b.conversions,
                        var_b.impressions,
                    )
                    rev_a = (
                        var_a.continuous_metrics.get("revenue", [])
                        if var_a.continuous_metrics
                        else []
                    )
                    rev_b = (
                        var_b.continuous_metrics.get("revenue", [])
                        if var_b.continuous_metrics
                        else []
                    )
                    all_a = rev_a + [0] * (var_a.impressions - len(rev_a))
                    all_b = rev_b + [0] * (var_b.impressions - len(rev_b))
                    if all_a and all_b:
                        t_test_results[f"rpv_{var_a.id}_vs_{var_b.id}"] = (
                            self.statistical_service.calculate_t_test(all_a, all_b)
                        )
            results["p_value"] = min(p_values) if p_values else 1.0
            results["effect_size"] = max(effect_sizes) if effect_sizes else 0.0
            results["t_test_results"] = t_test_results

        if include_segments:
            results["segment_winners"] = self.get_winners_by_segment(ab_test_id)
        return results

    def _get_segment_results_for_variant(self, variant_id: int) -> Dict[str, Any]:
        segment_performances = (
            self.db.query(SegmentPerformance)
            .options(selectinload(SegmentPerformance.segment))
            .filter(SegmentPerformance.variant_id == variant_id)
            .all()
        )
        structured_results = defaultdict(list)
        for perf in segment_performances:
            revenue_data = perf.revenue_data or []
            total_revenue = sum(revenue_data)
            aov = total_revenue / len(revenue_data) if revenue_data else 0
            rpv = total_revenue / perf.impressions if perf.impressions > 0 else 0
            structured_results[perf.segment.type].append(
                {
                    "segment_value": perf.segment.value,
                    "impressions": perf.impressions,
                    "conversions": perf.conversions,
                    "conversion_rate": (perf.conversions / perf.impressions) * 100
                    if perf.impressions > 0
                    else 0,
                    "total_revenue": total_revenue,
                    "average_order_value": aov,
                    "revenue_per_visitor": rpv,
                }
            )
        return structured_results

    def _get_variant_revenue_per_visitor(self, variant: Variant) -> float:
        """Helper to calculate revenue per visitor for a variant."""
        if not variant.impressions:
            return 0.0
        revenue_data = (
            variant.continuous_metrics.get("revenue", [])
            if variant.continuous_metrics
            else []
        )
        total_revenue = sum(revenue_data)
        return total_revenue / variant.impressions

    def get_winners_by_segment(
        self, ab_test_id: int, alpha: float = 0.05, min_impressions: int = 100
    ) -> Dict[str, Any]:
        ab_test = self.get_ab_test_by_id(ab_test_id)
        if not ab_test:
            return {}
        all_segments = (
            self.db.query(Segment)
            .join(SegmentPerformance)
            .filter(SegmentPerformance.variant.has(ab_test_id=ab_test_id))
            .distinct()
            .all()
        )
        segment_winners = defaultdict(dict)
        for segment in all_segments:
            segment_perfs = (
                self.db.query(SegmentPerformance)
                .join(Variant)
                .filter(
                    SegmentPerformance.segment_id == segment.id,
                    Variant.ab_test_id == ab_test_id,
                    SegmentPerformance.impressions >= min_impressions,
                )
                .options(selectinload(SegmentPerformance.variant))
                .all()
            )
            if len(segment_perfs) < 2:
                continue
            segment_perfs.sort(
                key=lambda p: (sum(p.revenue_data) / p.impressions)
                if (p.revenue_data and p.impressions > 0)
                else 0,
                reverse=True,
            )
            candidate_winner_perf = segment_perfs[0]
            is_significant_winner = True
            for other_perf in segment_perfs[1:]:
                revenue_winner = candidate_winner_perf.revenue_data or []
                revenue_other = other_perf.revenue_data or []
                all_visitors_winner = revenue_winner + [0] * (
                    candidate_winner_perf.impressions - len(revenue_winner)
                )
                all_visitors_other = revenue_other + [0] * (
                    other_perf.impressions - len(revenue_other)
                )
                if not all_visitors_winner or not all_visitors_other:
                    is_significant_winner = False
                    break
                p_value = self.statistical_service.calculate_t_test(
                    all_visitors_winner, all_visitors_other
                )
                if p_value >= alpha:
                    is_significant_winner = False
                    break
            if is_significant_winner:
                segment_winners[segment.type][segment.value] = {
                    "winner_variant_id": candidate_winner_perf.variant.id,
                    "description": candidate_winner_perf.variant.description,
                    "revenue_per_visitor": (
                        sum(candidate_winner_perf.revenue_data)
                        / candidate_winner_perf.impressions
                    )
                    if candidate_winner_perf.revenue_data
                    else 0,
                }
        return segment_winners

    def get_winner(
        self,
        ab_test_id: int,
        alpha: float = 0.05,
        min_conversions: int = 5,
        min_impressions: int = 30,
    ) -> Variant | None:
        ab_test = self.get_ab_test_by_id(ab_test_id)
        if not ab_test or len(ab_test.variants) < 2:
            return None

        self.flush_metrics()
        self.db.refresh(ab_test)
        self.calculate_conversion_rates(ab_test_id)
        self.db.refresh(ab_test)
        for v in ab_test.variants:
            self.db.refresh(v)

        # Sort by conversion rate as the primary key for determining the winner.
        variants = sorted(
            ab_test.variants,
            key=lambda v: (v.conversions / v.impressions) if v.impressions > 0 else 0,
            reverse=True,
        )

        if not variants:
            return None

        candidate_winner = variants[0]

        # Check for minimum thresholds for the top variant
        if (
            candidate_winner.impressions < min_impressions
            or candidate_winner.conversions < min_conversions
        ):
            return None

        # If there's only one other variant, check significance against it
        if len(variants) == 2:
            other_variant = variants[1]
            if (
                other_variant.impressions < min_impressions
                or other_variant.conversions < min_conversions
            ):
                # Not enough data for comparison, so no winner yet
                return None

            result = self.statistical_service.sequential_probability_ratio_test(
                c1=candidate_winner.conversions,
                n1=candidate_winner.impressions,
                c2=other_variant.conversions,
                n2=other_variant.impressions,
                alpha=alpha,
            )
            if result == "accept_h1":
                return candidate_winner
            else:
                # If not significant, there is no winner yet
                return None

        # For more than 2 variants, ensure the winner is better than all others
        is_significant_winner = True
        for other_variant in variants[1:]:
            if (
                other_variant.impressions < min_impressions
                or other_variant.conversions < min_conversions
            ):
                continue  # Skip comparison if the other variant lacks data

            result = self.statistical_service.sequential_probability_ratio_test(
                c1=candidate_winner.conversions,
                n1=candidate_winner.impressions,
                c2=other_variant.conversions,
                n2=other_variant.impressions,
                alpha=alpha,
            )
            if result != "accept_h1":
                is_significant_winner = False
                break

        if is_significant_winner:
            return candidate_winner

        return None

    async def check_and_declare_winner(self, ab_test_id: int):
        try:
            winner = self.get_winner(ab_test_id)
            if winner:
                ab_test = self.get_ab_test_by_id(ab_test_id)
                if not ab_test:
                    return
                user = self.db.get(ShopifyUser, ab_test.user_id)
                if user:
                    await self.declare_winner(ab_test_id, winner.id, user)
        except ValueError as e:
            logger.error(
                f"Error checking or declaring winner for test {ab_test_id}: {e}"
            )

    def rotate_and_update_shopify(self, ab_test_id: int):
        try:
            ab_test = self.get_ab_test_by_id(ab_test_id)
            if not ab_test or ab_test.status != ABTestStatus.RUNNING:
                return
            user = self.db.get(ShopifyUser, ab_test.user_id)
            if not user:
                return
            if not ab_test.variants:
                return
            current_active_index = -1
            if ab_test.active_variant_id:
                for i, variant in enumerate(ab_test.variants):
                    if variant.id == ab_test.active_variant_id:
                        current_active_index = i
                        break
            next_active_index = (current_active_index + 1) % len(ab_test.variants)
            next_variant = ab_test.variants[next_active_index]
            ab_test.active_variant_id = next_variant.id
            self.shopify_service.save_description(
                user=user,
                request=SaveRequest(
                    product_id=ab_test.product_id,
                    new_description=next_variant.description,
                ),
            )
            self.db.commit()
            logger.info(f"Rotated variant for test {ab_test_id} to {next_variant.id}")
        except Exception as e:
            logger.error(f"Failed to rotate variant for test {ab_test_id}: {e}")
            self.db.rollback()

    async def auto_optimize_cycle(self):
        logger.info("Starting auto-optimize cycle.")
        auto_tests = (
            self.db.query(ABTest)
            .filter(
                ABTest.auto_optimize == True,
                ABTest.status.in_([ABTestStatus.RUNNING, ABTestStatus.CONCLUDED]),
            )
            .all()
        )
        tasks = []
        for test in auto_tests:
            if test.status == ABTestStatus.RUNNING:
                tasks.append(self._check_and_promote_winner_for_auto_test(test))
            elif test.status == ABTestStatus.CONCLUDED:
                user = self.db.get(ShopifyUser, test.user_id)
                if not user:
                    logger.warning(
                        f"User not found for test {test.id}, skipping auto-optimize cycle."
                    )
                    continue
                tasks.append(self._consider_starting_new_challenger_test(test, user))
        if tasks:
            await asyncio.gather(*tasks)
        logger.info("Auto-optimize cycle finished.")

    async def _check_and_promote_winner_for_auto_test(self, test: ABTest):
        await self.check_and_declare_winner(test.id)

    async def _consider_starting_new_challenger_test(
        self, test: ABTest, user: ShopifyUser
    ):
        """Checks conditions and starts a new challenger test if applicable."""
        if not test.winner_variant_id:
            logger.info(
                f"Auto-optimize for test {test.id} skipped: No winner declared."
            )
            return

        cooldown_days = test.auto_optimize_cooldown_days or 0
        if test.end_time and (
            datetime.now(timezone.utc) - test.end_time.replace(tzinfo=timezone.utc)
        ) < timedelta(days=cooldown_days):
            logger.info(
                f"Auto-optimize for test {test.id} skipped: Cooldown period has not passed."
            )
            return

        champion_variant = self.db.get(Variant, test.winner_variant_id)
        if not champion_variant:
            logger.error(
                f"Champion variant {test.winner_variant_id} not found for test {test.id}."
            )
            return

        try:
            product_details = await self.shopify_service.get_product_details(
                user, test.product_id
            )
            new_variants_data = await self._generate_challenger_variants(
                champion_description=champion_variant.description,
                product_title=product_details.get("title"),
                product_tags=product_details.get("tags"),
            )
        except Exception as e:
            logger.error(
                f"Failed to generate AI challenger variants for product {test.product_id}: {e}"
            )
            return

        await self._create_new_challenger_test(
            test, user, champion_variant, new_variants_data
        )

    async def _create_new_challenger_test(
        self,
        test: ABTest,
        user: ShopifyUser,
        champion_variant: Variant,
        new_variants_data: list[dict],
    ):
        """Creates and launches a new challenger test within the async context."""
        try:
            # Mark the old test as no longer being part of the auto-optimize chain
            test.auto_optimize = False
            self.db.add(test)

            all_variants_data = [
                {"description": champion_variant.description, "is_control": True}
            ] + new_variants_data

            new_test = self.create_ab_test(
                user_id=user.id,
                product_id=test.product_id,
                name=f"Auto-Challenger for {test.product_id}",
                description=f"Automated follow-up test for '{test.name}'",
                test_type=test.test_type,
                variants_data=all_variants_data,
                auto_optimize=True,
                auto_optimize_cooldown_days=test.auto_optimize_cooldown_days,
                start_time=datetime.now(timezone.utc),
                db=self.db,
            )
            self.update_ab_test_status(
                new_test.id, ABTestStatus.DRAFT, user.id, db=self.db
            )
            self.db.commit()
            logger.info(
                f"Successfully created and launched new auto-challenger test {new_test.id}"
            )
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in _create_new_challenger_test: {e}")
            raise

    async def generate_test_hypothesis(
        self, user: ShopifyUser, num_months_history: int = 6
    ) -> dict:
        """
        Analyzes historical A/B test performance to generate strategic, high-level test hypotheses.
        """
        now = datetime.now(timezone.utc)
        history_start_date = now - timedelta(days=30 * num_months_history)

        past_tests = (
            self.db.query(ABTest)
            .filter(
                ABTest.user_id == user.id,
                ABTest.status == ABTestStatus.CONCLUDED,
                ABTest.end_time >= history_start_date,
            )
            .options(selectinload(ABTest.variants))
            .all()
        )

        if not past_tests:
            # If no history, find the best-selling product to suggest a first test.
            try:
                loop = asyncio.get_running_loop()
                best_seller_id = await loop.run_in_executor(
                    None, self.analytics_service.get_best_selling_product_id, user.id
                )
                if best_seller_id:
                    return {
                        "hypothesis": "No test history found. A great starting point is to optimize your best-selling product. Let's test a new description focused on its key benefits.",
                        "suggested_product_id": str(best_seller_id),
                        "type": "description",
                        "analysis": "Initial test on best-selling product.",
                    }
            except Exception as e:
                logger.error(
                    f"Could not fetch best-selling product for initial hypothesis: {e}"
                )
            # Fallback to a generic suggestion if analytics fail
            return {
                "hypothesis": "No conclusive test history found. A good starting point is to test different emotional vs. functional headlines on a popular product.",
                "suggested_product_id": None,
                "type": "title",
                "analysis": "Default suggestion due to no test history and analytics failure.",
            }

        summary_items = []
        for test in past_tests:
            winner = (
                self.db.get(Variant, test.winner_variant_id)
                if test.winner_variant_id
                else None
            )
            if not winner:
                continue

            # Find the control variant to compare against
            control = next((v for v in test.variants if v.is_control), None)
            if not control or control.id == winner.id:
                # Robust fallback: if no explicit control, find the variant with the most impressions,
                # as it's the most likely de-facto control. Avoids sorting by conversion rate which might be 0.
                non_winner_variants = [v for v in test.variants if v.id != winner.id]
                if not non_winner_variants:
                    continue  # Skip if winner was the only variant
                control = sorted(
                    non_winner_variants, key=lambda v: v.impressions, reverse=True
                )[0]

            winner_cr = (
                (winner.conversions / winner.impressions) * 100
                if winner.impressions > 0
                else 0
            )
            control_cr = (
                (control.conversions / control.impressions) * 100
                if control.impressions > 0
                else 0
            )
            uplift = winner_cr - control_cr

            summary_items.append(
                f"- Test on Product ID {test.product_id}: The winning approach was '{winner.description[:60].strip()}...' which achieved a {winner_cr:.2f}% conversion rate, "
                f"beating '{control.description[:60].strip()}...' (at {control_cr:.2f}%) with an uplift of {uplift:.2f} percentage points."
            )

        history_summary = "\n".join(summary_items)

        prompt = f"""
        You are a world-class A/B testing strategist for a Shopify store.
        Analyze the following summary of past A/B test results to identify underlying patterns and propose a new, strategic test hypothesis.

        **Past Test Performance:**
        {history_summary}

        **Your Task:**
        1.  **Analyze:** Briefly explain the pattern you've identified. What seems to be working (e.g., shorter titles, scarcity, benefit-focused descriptions)?
        2.  **Hypothesize:** Formulate a clear, strategic hypothesis for the *next* A/B test.
        3.  **Suggest:** Recommend a specific 'type' of test ('title', 'description', or 'price') and a 'product_id' from the history that would be a good candidate for this new test. If no specific product stands out, return the most frequently tested one.

        Return a single, valid JSON object with the following keys: "analysis", "hypothesis", "type", "suggested_product_id".

        Example Response:
        {{
            "analysis": "Descriptions that create a sense of urgency or scarcity have consistently outperformed longer, story-based descriptions.",
            "hypothesis": "We hypothesize that applying the principle of scarcity to product descriptions across other products will lead to a similar uplift in conversion rates.",
            "type": "description",
            "suggested_product_id": "84329102"
        }}
        """
        try:
            response = await self._openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a data-driven A/B testing strategist providing analysis in JSON format.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.7,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            ai_response = json.loads(content)

            # Find the most common product ID from the history as a fallback
            if not ai_response.get("suggested_product_id") and past_tests:
                product_ids = [test.product_id for test in past_tests]
                ai_response["suggested_product_id"] = max(
                    set(product_ids), key=product_ids.count
                )

            return ai_response

        except (json.JSONDecodeError, IndexError) as e:
            logger.error(f"Error decoding or parsing hypothesis from OpenAI: {e}")
            raise ValueError("Failed to generate a valid hypothesis from AI.") from e
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while generating hypothesis: {e}"
            )
            raise

    async def create_ai_driven_test(
        self, user: ShopifyUser, num_variants: int = 2
    ) -> ABTest:
        """
        Orchestrates the creation of a new A/B test using a two-layered AI approach.
        1. Generates a strategic hypothesis based on past performance.
        2. Generates tactical variants based on that hypothesis.
        3. Creates and starts the new A/B test.
        """
        # 1. Get strategic hypothesis
        hypothesis_data = await self.generate_test_hypothesis(user)
        if not hypothesis_data.get("suggested_product_id"):
            raise LookupError(
                "AI failed to suggest a product for testing. Insufficient historical or sales data."
            )

        product_id = hypothesis_data["suggested_product_id"]
        test_type = hypothesis_data["type"]
        test_description = hypothesis_data["hypothesis"]

        # 2. Get tactical variants using the existing AI service
        recommendation_for_variant_gen = {
            "type": test_type,
            "description": test_description,
        }

        # Note: The `generate_variants` method in AIRecommendationsService expects an integer product_id.
        # We ensure the type is correct before calling.
        try:
            product_id_int = int(product_id)
        except (ValueError, TypeError):
            raise TypeError(
                f"Invalid Product ID: '{product_id}'. Must be a valid integer."
            )

        loop = asyncio.get_running_loop()
        generated_variants = await loop.run_in_executor(
            None,  # Uses the default ThreadPoolExecutor
            self.ai_recommendations_service.generate_variants,
            user,
            product_id_int,
            recommendation_for_variant_gen,
            num_variants,
        )

        if not generated_variants:
            raise ConnectionError(
                "AI failed to generate test variants for the given hypothesis."
            )

        # 3. Get the current product state to create the control variant
        # The `get_product` method is also not async and expects an integer.
        product = await loop.run_in_executor(
            None, self.shopify_service.get_product, user, product_id_int
        )
        if not product:
            raise FileNotFoundError(
                f"Could not retrieve product details for product ID {product_id_int}."
            )

        # Determine which field to use for the control
        control_content = ""
        if test_type == "title":
            control_content = product.get("title", "")
        elif test_type == "description":
            control_content = product.get("body_html", "")
        elif test_type == "price":
            if product.get("variants"):
                control_content = product["variants"][0].get("price", "0.00")

        # 4. Assemble variants and create the test
        variants_data = [{"description": control_content, "is_control": True}]
        for variant in generated_variants:
            variants_data.append(
                {"description": variant["description"], "is_control": False}
            )

        new_test = self.create_ab_test(
            user_id=user.id,
            product_id=str(product_id),
            name=f"AI-driven test for {product_id}",
            description=test_description,
            variants_data=variants_data,
            test_type=test_type,
            auto_optimize=False,  # Default to false for AI-driven tests
        )

        # Start the test immediately
        if new_test:
            self.update_ab_test_status(new_test.id, ABTestStatus.RUNNING, user.id)
            logger.info(
                f"Successfully created and started AI-driven A/B test {new_test.id} for product {product_id}."
            )

        return new_test

    async def _generate_challenger_variants(
        self, champion_description: str, product_title: str, product_tags: list[str]
    ) -> list[dict]:
        """Generates new challenger variants using an AI model."""
        prompt = f"""
        Given the winning A/B test variant for a product, generate two new, distinct, and creative challenger variants.
        Product Title: {product_title}
        Product Tags: {", ".join(product_tags)}
        Winning Variant Description:
        ---
        {champion_description}
        ---
        Generate two new descriptions as a JSON object with a single key "variants" which is a list of strings.
        Example format: {{"variants": ["New Description 1", "New Description 2"]}}
        """
        try:
            response = await self._openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.7,
            )
            content = response.choices[0].message.content
            variants_json = json.loads(content)

            if "variants" not in variants_json or not isinstance(
                variants_json["variants"], list
            ):
                raise ValueError(
                    "Invalid JSON structure from AI: 'variants' key missing or not a list."
                )

            return [
                {"description": desc, "is_control": False}
                for desc in variants_json["variants"]
            ]

        except json.JSONDecodeError:
            logger.error("Failed to decode JSON from AI response.")
            return []
        except Exception as e:
            logger.error(
                f"An unexpected error occurred while generating challenger variants: {e}"
            )
            return []
