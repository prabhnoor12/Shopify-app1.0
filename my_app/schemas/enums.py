"""
This module defines shared enumerations used across the application for status fields
and other categorical data. Using enums helps ensure data consistency and makes the
code more readable and maintainable.
"""

from enum import Enum


class ProductStatus(str, Enum):
    """
    Represents the lifecycle and health status of a product within our system.
    """

    SYNCED = "synced"  # Product is in sync with Shopify and no issues are detected.
    NEEDS_REVIEW = "needs_review"  # AI content has been generated and is awaiting user approval.
    GENERATING = "generating"  # AI content generation is in progress.
    ERROR = "error"  # An error occurred during a process (e.g., generation, sync).
    NEEDS_ATTENTION = "needs_attention"  # The content audit has flagged an issue with this product.
