"""
Service layer for handling content versioning.
"""

import logging
from sqlalchemy.orm import Session
from typing import List

from ..crud import content_version_crud
from ..models.product import Product
from ..models.content_version import ContentVersion
from ..schemas.content_version import ContentVersionCreate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContentVersionService:
    """
    Service for managing content versions.
    """

    def __init__(self, db: Session):
        """
        Initializes the ContentVersionService.

        Args:
            db (Session): The SQLAlchemy database session.
        """
        self.db = db

    def create_version_from_product(
        self, product: Product, user_id: int, reason: str = "Product Update"
    ) -> ContentVersion:
        """
        Creates a new content version from a product object.

        Args:
            product (Product): The product to version.
            user_id (int): The ID of the user performing the action.
            reason (str): The reason for the new version.

        Returns:
            ContentVersion: The created content version.
        """
        logger.info(
            f"Creating content version for product {product.id} by user {user_id}"
        )

        # Find the latest version number for the product
        latest_version = self.get_latest_version_number(product.id)
        new_version_number = latest_version + 1

        version_data = ContentVersionCreate(
            product_id=product.id,
            version=new_version_number,
            title=product.title,
            body_html=product.body_html,
            updated_by_id=user_id,
            reason_for_change=reason,
        )
        return content_version_crud.create_content_version(self.db, version_data)

    def get_versions_for_product(self, product_id: int) -> List[ContentVersion]:
        """
        Retrieves all content versions for a given product.

        Args:
            product_id (int): The ID of the product.

        Returns:
            List[ContentVersion]: A list of content versions.
        """
        logger.info(f"Fetching content versions for product {product_id}")
        return content_version_crud.get_content_versions_by_product_id(
            self.db, product_id
        )

    def get_latest_version_number(self, product_id: int) -> int:
        """
        Gets the latest version number for a product.

        Args:
            product_id (int): The ID of the product.

        Returns:
            int: The latest version number, or 0 if no versions exist.
        """
        versions = self.get_versions_for_product(product_id)
        if not versions:
            return 0
        return max(v.version for v in versions)

    def revert_to_version(self, content_version_id: int):
        # This would be implemented later, along with the corresponding ProductService method
        # and API endpoint.
        pass
