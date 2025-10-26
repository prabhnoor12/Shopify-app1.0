"""
This module contains CRUD operations for fetching analytics data.
"""

from sqlalchemy.orm import Session
from datetime import datetime
from .. import models


def get_content_generation_count(
    db: Session, shop_id: int, start_date: datetime, end_date: datetime
) -> int:
    """
    Counts the number of content generations for a specific shop within a date range.
    This assumes a Usage model exists with a 'shop_id', a 'feature_name' and a 'created_at' timestamp.
    """
    count = (
        db.query(models.Usage)
        .filter(
            models.Usage.shop_id == shop_id,
            models.Usage.feature_name == "product_description_generation",
            models.Usage.created_at >= start_date,
            models.Usage.created_at <= end_date,
        )
        .count()
    )
    return count


def get_completed_ab_tests_count(
    db: Session, shop_id: int, start_date: datetime, end_date: datetime
) -> int:
    """
    Counts the number of completed A/B tests for a specific shop within a date range.
    Assumes an ABTest model exists with a 'shop_id', 'status', and 'end_date'.
    """
    count = (
        db.query(models.ABTest)
        .filter(
            models.ABTest.shop_id == shop_id,
            models.ABTest.status == "COMPLETED",
            models.ABTest.end_date >= start_date,
            models.ABTest.end_date <= end_date,
        )
        .count()
    )
    return count
