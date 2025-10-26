from collections import defaultdict
from datetime import datetime, timedelta, timezone
from functools import lru_cache
import math
from typing import List, Dict, Any, Optional

from sqlalchemy import func, case, String
from sqlalchemy.orm import Session
from openai import OpenAI

from ..models.shop import ShopifyUser
from ..models.ab_test import ABTest
from ..models.variant import Variant
from ..models.user import User
from ..models.product import Product
from ..models.audit import AuditLog
from ..services.shop_service import ShopifyService
from .seo_service import SEOService


# Constants for actionable alerts
MIN_IMPRESSIONS_FOR_ALERT = 200
LOW_CONVERSION_RATE_THRESHOLD = 0.5
MIN_IMPRESSIONS_FOR_WINNER = 100
WINNER_LIFT_THRESHOLD = 2.0  # 2x better
HIGH_TRAFFIC_THRESHOLD = 500
CONFIDENCE_LEVEL_Z_SCORE = 1.96  # For 95% confidence


class MerchantAnalyticsService:
    """
    Provides actionable, visual, and revenue-tied analytics for merchants.
    Enhanced for robustness, performance, and deeper insights.
    """

    def __init__(
        self,
        db: Session,
        shopify_service: ShopifyService,
        openai_client: OpenAI,
        seo_service: SEOService,
    ):
        self.db = db
        self.shopify_service = shopify_service
        self.openai_client = openai_client
        self.seo_service = seo_service

    @lru_cache(maxsize=128)
    def get_revenue_attribution(
        self, user: ShopifyUser, product_id: int
    ) -> Dict[str, Any]:
        """
        Calculates the total revenue attributed to a specific product.
        Now with caching to improve performance for repeated calls.
        """
        orders = self.shopify_service.fetch_orders_for_product(user, product_id)

        total_revenue = sum(float(order.get("total_price", 0.0)) for order in orders)
        total_subtotal = sum(
            float(order.get("subtotal_price", 0.0)) for order in orders
        )
        total_tax = sum(float(order.get("total_tax", 0.0)) for order in orders)
        total_discounts = sum(
            float(order.get("total_discounts", 0.0)) for order in orders
        )
        order_count = len(orders)

        return {
            "product_id": product_id,
            "total_revenue": round(total_revenue, 2),
            "total_subtotal": round(total_subtotal, 2),
            "total_tax": round(total_tax, 2),
            "total_discounts": round(total_discounts, 2),
            "total_orders": order_count,
            "average_order_value": round(total_revenue / order_count, 2)
            if order_count > 0
            else 0.0,
        }

    def get_description_performance(
        self, user: ShopifyUser, product_id: int
    ) -> List[Dict[str, Any]]:
        """
        Analyzes the performance of A/B test variants for a product, including revenue.
        """
        ab_test = (
            self.db.query(ABTest)
            .filter(ABTest.product_id == product_id, ABTest.user_id == user.id)
            .first()
        )
        if not ab_test:
            return []

        variants = self.db.query(Variant).filter(Variant.ab_test_id == ab_test.id).all()
        if not variants:
            return []

        total_conversions = sum(v.conversions for v in variants if v.conversions)
        revenue_data = self.get_revenue_attribution(user, product_id)
        total_revenue = revenue_data.get("total_revenue", 0)

        # Identify baseline variant (assuming it's the one with the lowest ID)
        baseline_variant = min(variants, key=lambda v: v.id) if variants else None
        baseline_cr = (
            (baseline_variant.conversions / baseline_variant.impressions)
            if baseline_variant and baseline_variant.impressions > 0
            else 0.0
        )

        performance_data = []
        for variant in variants:
            conversion_rate = (
                (variant.conversions / variant.impressions) * 100
                if variant.impressions > 0
                else 0.0
            )
            revenue_share = (
                (variant.conversions / total_conversions) * total_revenue
                if total_conversions > 0
                else 0
            )

            # Calculate confidence interval for the conversion rate
            ci_lower, ci_upper = self._calculate_confidence_interval(
                variant.conversions, variant.impressions
            )

            # Calculate lift over baseline
            lift_over_baseline = (
                ((conversion_rate / 100 - baseline_cr) / baseline_cr) * 100
                if baseline_cr > 0 and variant.id != baseline_variant.id
                else 0.0
            )

            # Calculate p-value for statistical significance
            p_value = self._calculate_p_value(baseline_variant, variant) if baseline_variant and variant.id != baseline_variant.id else None

            performance_data.append(
                {
                    "variant_id": variant.id,
                    "description": variant.description,
                    "impressions": variant.impressions,
                    "clicks": variant.clicks,
                    "conversions": variant.conversions,
                    "conversion_rate": round(conversion_rate, 2),
                    "confidence_interval": (round(ci_lower, 2), round(ci_upper, 2)),
                    "lift_over_baseline": round(lift_over_baseline, 2),
                    "is_baseline": variant.id == baseline_variant.id,
                    "estimated_revenue": round(revenue_share, 2),
                    "p_value": p_value,
                }
            )
        return performance_data

    def analyze_seo(
        self,
        primary_keyword: str,
        title: str,
        description: str,
        meta_title: Optional[str] = None,
        meta_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Performs an advanced SEO analysis of product content by calling the centralized SEO service.
        """
        return self.seo_service.analyze_seo(
            primary_keyword=primary_keyword,
            title=title,
            description=description,
            meta_title=meta_title,
            meta_description=meta_description,
        )

    def generate_seo_improvement_suggestions(
        self, analysis_results: Dict[str, Any]
    ) -> str:
        """
        Uses AI to generate actionable suggestions by calling the centralized SEO service.
        """
        return self.seo_service.generate_seo_improvement_suggestions(
            openai_client=self.openai_client, analysis_results=analysis_results
        )

    def get_product_timeline_performance(
        self, user: ShopifyUser, product_id: int, days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get product timeline performance data."""
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=days)

        # Create a date range to ensure all days are included in the output
        # The range should be `days + 1` to include both start and end dates.
        date_range = [start_date + timedelta(days=i) for i in range(days + 1)]
        date_map = {
            date.isoformat(): {
                "date": date.isoformat(),
                "views": 0,
                "adds_to_cart": 0,
            }
            for date in date_range
        }

        # Query for product performance timeline data
        query = (
            self.db.query(
                func.date(AuditLog.created_at).label("date"),
                func.count(case((AuditLog.action == "view_product", 1))).label("views"),
                func.count(case((AuditLog.action == "add_to_cart", 1))).label(
                    "adds_to_cart"
                ),
            )
            .filter(
                AuditLog.user_id == user.user_id,
                AuditLog.target_id == str(product_id),
                AuditLog.target_entity == "product",
                func.date(AuditLog.created_at).between(start_date, end_date),
            )
            .group_by(func.date(AuditLog.created_at))
            .order_by(func.date(AuditLog.created_at))
        )

        timeline_events = query.all()

        # Populate the date map with real data
        for event in timeline_events:
            # Ensure event.date is a date object before calling isoformat
            if hasattr(event.date, 'isoformat'):
                date_iso = event.date.isoformat()
                if date_iso in date_map:
                    date_map[date_iso]["views"] = event.views
                    date_map[date_iso]["adds_to_cart"] = event.adds_to_cart

        # Sort the results by date before returning
        return sorted(list(date_map.values()), key=lambda x: x['date'])

    def get_team_performance(self, team_id: int) -> List[Dict[str, Any]]:
        """
        Provides comprehensive performance metrics for each member of a team, optimized to avoid N+1 queries.
        """
        team_members = self.db.query(User).filter(User.team_id == team_id).all()
        if not team_members:
            return []

        member_ids = [member.id for member in team_members]

        # Query for audit-related stats (descriptions generated/published)
        audit_stats = (
            self.db.query(
                AuditLog.user_id,
                func.sum(
                    case((AuditLog.action == "generate_description", 1), else_=0)
                ).label("descriptions_generated"),
                func.sum(
                    case((AuditLog.action == "publish_description", 1), else_=0)
                ).label("descriptions_published"),
            )
            .filter(AuditLog.user_id.in_([member.id for member in team_members]))
            .group_by(AuditLog.user_id)
            .all()
        )

        product_stats = (
            self.db.query(
                User.id.label("user_id"),
                func.count(Product.id).label("products_managed"),
            )
            .join(ShopifyUser, User.id == ShopifyUser.user_id)
            .join(Product, ShopifyUser.id == Product.shop_id)
            .filter(User.id.in_(member_ids))
            .group_by(User.id)
            .all()
        )

        audit_map = {stat.user_id: stat for stat in audit_stats}
        product_map = {stat.user_id: stat for stat in product_stats}

        # Calculate average conversion rates for each team member
        conversion_rate_stats = (
            self.db.query(
                User.id.label("user_id"),
                func.sum(Variant.conversions).label("total_conversions"),
                func.sum(Variant.impressions).label("total_impressions"),
            )
            .join(ShopifyUser, User.id == ShopifyUser.user_id)
            .join(Product, ShopifyUser.id == Product.shop_id)
            .join(ABTest, ABTest.product_id == Product.id)
            .join(Variant, Variant.ab_test_id == ABTest.id)
            .filter(User.id.in_(member_ids))
            .group_by(User.id)
            .all()
        )

        conversion_rate_map = {
            stat.user_id: (stat.total_conversions / stat.total_impressions) * 100
            if stat.total_impressions > 0
            else 0.0
            for stat in conversion_rate_stats
        }

        performance_data = []
        for member in team_members:
            member_audit = audit_map.get(member.id)
            member_product = product_map.get(member.id)
            avg_conversion_rate = conversion_rate_map.get(member.id, 0.0)
            performance_data.append(
                {
                    "user_id": member.id,
                    "user_name": member.name,
                    "descriptions_generated": member_audit.descriptions_generated
                    if member_audit
                    else 0,
                    "descriptions_published": member_audit.descriptions_published
                    if member_audit
                    else 0,
                    "products_managed": member_product.products_managed
                    if member_product
                    else 0,
                    "average_conversion_rate": round(avg_conversion_rate, 2),
                }
            )
        return performance_data

    def get_category_performance(self, user: ShopifyUser) -> List[Dict[str, Any]]:
        """
        Provides aggregated analytics for each product category.
        Returns a list of dicts with category name, product count, total views, total conversions, and average conversion rate.
        """
        # Assume Product has a 'category' field
        results = (
            self.db.query(
                Product.category,
                func.count(Product.id).label("product_count"),
                func.sum(func.coalesce(AuditLog.id, 0)).label("total_views"),
                func.sum(func.coalesce(Variant.conversions, 0)).label("total_conversions"),
                func.sum(func.coalesce(Variant.impressions, 0)).label("total_impressions")
            )
            .outerjoin(AuditLog, (AuditLog.target_id == func.cast(Product.id, String)) & (AuditLog.action == "view_product"))
            .outerjoin(ABTest, ABTest.product_id == Product.id)
            .outerjoin(Variant, Variant.ab_test_id == ABTest.id)
            .filter(Product.shop_id == user.id)
            .group_by(Product.category)
            .all()
        )
        category_data = []
        for row in results:
            avg_conversion_rate = (row.total_conversions / row.total_impressions * 100) if row.total_impressions else 0.0
            category_data.append({
                "category": row.category,
                "product_count": row.product_count,
                "total_views": row.total_views,
                "total_conversions": row.total_conversions,
                "average_conversion_rate": round(avg_conversion_rate, 2)
            })
        return category_data

    def _calculate_confidence_interval(
        self, conversions: int, impressions: int
    ) -> tuple[float, float]:
        """
        Calculates the confidence interval for a conversion rate using the Wilson score interval.
        This is more reliable for small numbers of trials and extreme probabilities.
        """
        if impressions == 0:
            return 0.0, 0.0

        z = CONFIDENCE_LEVEL_Z_SCORE
        p = conversions / impressions
        n = impressions

        denominator = 1 + z**2 / n
        centre_adjusted_probability = p + z**2 / (2 * n)
        adjusted_standard_error = math.sqrt(
            (p * (1 - p) + z**2 / (4 * n)) / n
        )

        lower_bound = (
            centre_adjusted_probability - z * adjusted_standard_error
        ) / denominator
        upper_bound = (
            centre_adjusted_probability + z * adjusted_standard_error
        ) / denominator

        return lower_bound * 100, upper_bound * 100

    def _is_winner_statistically_significant(self, variant1, variant2) -> bool:
        """
        Performs a Z-test for proportions to determine if the difference in conversion
        rates is statistically significant.
        """
        if variant1["impressions"] == 0 or variant2["impressions"] == 0:
            return False

        p1 = variant1["conversions"] / variant1["impressions"]
        p2 = variant2["conversions"] / variant2["impressions"]
        n1 = variant1["impressions"]
        n2 = variant2["impressions"]

        if n1 + n2 == 0:
            return False

        p_pool = (variant1["conversions"] + variant2["conversions"]) / (n1 + n2)
        if p_pool == 0 or p_pool == 1:
            return False

        se_pool = (
            math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
            if n1 > 0 and n2 > 0
            else 0
        )
        if se_pool == 0:
            return False

        z_score = (p1 - p2) / se_pool
        return abs(z_score) > CONFIDENCE_LEVEL_Z_SCORE

    def _calculate_p_value(self, baseline_variant, variant) -> Optional[float]:
        """
        Calculates the p-value for the difference in conversion rates between two variants.
        Uses the Z-score calculated from the conversion rates and the pooled standard error.
        """
        if not baseline_variant or baseline_variant.impressions == 0 or variant.impressions == 0:
            return None  # Cannot determine significance

        p1 = baseline_variant.conversions / baseline_variant.impressions
        p2 = variant.conversions / variant.impressions
        n1 = baseline_variant.impressions
        n2 = variant.impressions

        if (n1 + n2) == 0:
            return None

        p_pool = (baseline_variant.conversions + variant.conversions) / (n1 + n2)

        if p_pool == 0 or p_pool == 1:
            return None

        se_pool = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))

        if se_pool == 0:
            return None

        z_score = (p1 - p2) / se_pool

        # Two-tailed p-value
        p_value = 2 * (1 - self._norm_cdf(abs(z_score)))
        return p_value

    def _norm_cdf(self, x: float) -> float:
        """
        Cumulative distribution function for the standard normal distribution.
        """
        return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

    def check_for_actionable_alerts(self, user: ShopifyUser) -> List[str]:
        """
        Checks for underperforming descriptions or A/B test results and returns actionable alerts.
        Optimized for large catalogs using bulk queries.
        """
        alerts = []

        # Bulk query for product view counts and categories
        product_view_counts = (
            self.db.query(
                Product.id,
                Product.title,
                Product.category,
                func.count(AuditLog.id).label("view_count")
            )
            .outerjoin(AuditLog, (AuditLog.target_id == func.cast(Product.id, String)) & (AuditLog.action == "view_product"))
            .filter(Product.shop_id == user.id)
            .group_by(Product.id, Product.title, Product.category)
            .all()
        )

        # Bulk query for A/B test performance data
        ab_test_performance = (
            self.db.query(
                Product.id.label("product_id"),
                Product.title,
                Product.category,
                Variant.id.label("variant_id"),
                Variant.impressions,
                Variant.conversions
            )
            .join(ABTest, ABTest.product_id == Product.id)
            .join(Variant, Variant.ab_test_id == ABTest.id)
            .filter(Product.shop_id == user.id)
            .all()
        )

        # Map product_id to view counts and category
        view_counts_map = {item.id: item for item in product_view_counts}

        # Group variants by product
        product_variants = defaultdict(list)
        for row in ab_test_performance:
            product_variants[row.product_id].append(row)

        # Alert for high-traffic products with no A/B test
        for product_id, view_info in view_counts_map.items():
            if view_info.view_count >= HIGH_TRAFFIC_THRESHOLD and product_id not in product_variants:
                alerts.append(f"Opportunity: Product '{view_info.title}' (Category: '{view_info.category}') has high traffic ({view_info.view_count} views) but no active A/B test.")

        # Alert for underperforming variants (bulk)
        for product_id, variants in product_variants.items():
            if not variants:
                continue
            # Find baseline (lowest id)
            baseline = min(variants, key=lambda v: v.variant_id)
            product_info = view_counts_map.get(product_id)
            product_title = product_info.title if product_info else "N/A"
            product_category = product_info.category if product_info else "N/A"

            for variant in variants:
                if variant.variant_id == baseline.variant_id:
                    continue
                # Calculate conversion rates
                baseline_cr = (baseline.conversions / baseline.impressions) if baseline.impressions else 0.0
                variant_cr = (variant.conversions / variant.impressions) if variant.impressions else 0.0
                # Calculate lift
                lift = ((variant_cr - baseline_cr) / baseline_cr * 100) if baseline_cr > 0 else 0.0
                # Statistical significance
                p_value = self._calculate_p_value(baseline, variant)
                if variant.impressions >= MIN_IMPRESSIONS_FOR_WINNER and lift > WINNER_LIFT_THRESHOLD and p_value is not None and p_value < 0.05:
                    alerts.append(f"Winner: Variant {variant.variant_id} for product '{product_title}' (Category: '{product_category}') is a statistically significant winner (lift: {lift:.2f}%, p-value: {p_value:.4f}).")
                elif variant.impressions >= MIN_IMPRESSIONS_FOR_ALERT and variant_cr < LOW_CONVERSION_RATE_THRESHOLD:
                    alerts.append(f"Alert: Variant {variant.variant_id} for product '{product_title}' (Category: '{product_category}') has low conversion rate ({variant_cr:.2%}).")
        return alerts
