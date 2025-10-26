"""
CRUD operations for the ContentVersion model.
"""

from sqlalchemy.orm import Session
from typing import List, Optional

from ..models.content_version import ContentVersion
from ..schemas.content_version import ContentVersionCreate


def create_content_version(
    db: Session, content_version: ContentVersionCreate
) -> ContentVersion:
    """
    Create a new content version.
    """
    db_content_version = ContentVersion(**content_version.dict())
    db.add(db_content_version)
    db.commit()
    db.refresh(db_content_version)
    return db_content_version


def get_content_versions_by_product_id(
    db: Session, product_id: int
) -> List[ContentVersion]:
    """
    Get all content versions for a specific product.
    """
    return (
        db.query(ContentVersion)
        .filter(ContentVersion.product_id == product_id)
        .order_by(ContentVersion.version.desc())
        .all()
    )


def get_content_version(
    db: Session, content_version_id: int
) -> Optional[ContentVersion]:
    """
    Get a specific content version by its ID.
    """
    return (
        db.query(ContentVersion).filter(ContentVersion.id == content_version_id).first()
    )
