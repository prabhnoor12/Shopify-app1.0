"""
API endpoints for content versioning.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..schemas.content_version import ContentVersion as ContentVersionSchema
from ..services.content_version_service import ContentVersionService

router = APIRouter()


@router.get(
    "/products/{product_id}/versions",
    response_model=List[ContentVersionSchema],
    tags=["Content Versioning"],
)
def list_product_content_versions(product_id: int, db: Session = Depends(get_db)):
    """
    Retrieve the content version history for a specific product.
    """
    content_version_service = ContentVersionService(db)
    versions = content_version_service.get_versions_for_product(product_id)
    if not versions:
        raise HTTPException(
            status_code=404, detail="No content versions found for this product."
        )
    return versions
