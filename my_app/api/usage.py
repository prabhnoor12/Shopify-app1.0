from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..services.usage_service import (
    UsageService,
)  # Changed from..services.usage_service import UsageService
from ..schemas.usage import UsageResponse
from ..database import get_db  # Changed from ..dependencies
from ..dependencies.auth import get_current_user
from ..models.shop import ShopifyUser

router = APIRouter(prefix="/usage", tags=["Usage"])


@router.get("/", response_model=UsageResponse)
def get_usage_stats(
    db: Session = Depends(get_db), current_user: ShopifyUser = Depends(get_current_user)
):
    """
    Retrieves the current usage statistics for the authenticated user's shop.
    """
    usage_service = UsageService(db)
    usage_data = usage_service.get_user_usage(current_user.user_id)
    return usage_data
