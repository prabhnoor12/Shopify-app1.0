from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import logging

from ..database import get_db
from ..utils.security import get_current_user
from ..models.shop import ShopifyUser
from ..schemas.shop_dynamic import DynamicContentRequest, DynamicContentResponse
from ..services.shop_dynamic import ShopDynamicService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/api/dynamic-content",
    response_model=DynamicContentResponse,
    summary="Get Real-Time Personalized Content",
    tags=["Storefront"],
)
async def get_dynamic_content(
    request: DynamicContentRequest,
    db: Session = Depends(get_db),
    user: ShopifyUser = Depends(get_current_user),
):
    """
    This endpoint provides real-time, personalized content snippets for a product
    description based on visitor data.

    It should be called by the Shopify storefront's theme JavaScript.

    - **Geolocation**: Returns different text based on visitor's country.
    - **Scarcity**: Provides urgency messaging for low-stock items.
    - **Social Proof**: Shows mocked-up data for recent views and purchases.
    """
    service = ShopDynamicService(db)
    try:
        response = await service.get_dynamic_content(user, request)
        return response
    finally:
        await service.close()
