from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from openai import OpenAI

from .. import database
from ..services.analytics_service import MerchantAnalyticsService
from ..services.shop_service import ShopifyService
from ..models.shop import ShopifyUser
from ..dependencies.auth import get_current_user
from ..dependencies.openai_client import get_openai_client

router = APIRouter(prefix="/merchant/analytics", tags=["merchant-analytics"])


class SEOAnalysisRequest(BaseModel):
    primary_keyword: str
    title: str
    description: str
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


def get_merchant_analytics_service(
    db: Session = Depends(database.get_db),
    openai_client: OpenAI = Depends(get_openai_client),
) -> MerchantAnalyticsService:
    shopify_service = ShopifyService(db, openai_client)
    return MerchantAnalyticsService(db, shopify_service, openai_client)


@router.get("/revenue-attribution/{product_id}", response_model=Dict)
async def get_revenue_attribution(
    product_id: int,
    user: ShopifyUser = Depends(get_current_user),
    service: MerchantAnalyticsService = Depends(get_merchant_analytics_service),
):
    """
    Get revenue attribution for a product.
    """
    return await service.get_revenue_attribution(user, product_id)


@router.get("/description-performance/{product_id}", response_model=List[Dict])
async def get_description_performance(
    product_id: int,
    user: ShopifyUser = Depends(get_current_user),
    service: MerchantAnalyticsService = Depends(get_merchant_analytics_service),
):
    """
    Get performance metrics for A/B test variants of a product description.
    """
    return await service.get_description_performance(user, product_id)


@router.post("/analyze-seo", response_model=Dict)
def analyze_seo(
    request: SEOAnalysisRequest,
    service: MerchantAnalyticsService = Depends(get_merchant_analytics_service),
):
    """
    Get an advanced SEO analysis for product content.
    """
    return service.analyze_seo(
        primary_keyword=request.primary_keyword,
        title=request.title,
        description=request.description,
        meta_title=request.meta_title,
        meta_description=request.meta_description,
    )


@router.get("/product-timeline-performance/{product_id}", response_model=List[Dict])
async def get_product_timeline_performance(
    product_id: int,
    user: ShopifyUser = Depends(get_current_user),
    days: int = 90,
    service: MerchantAnalyticsService = Depends(get_merchant_analytics_service),
):
    """
    Get timeline performance for a product.
    """
    return await service.get_product_timeline_performance(user, product_id, days)


@router.get("/team-performance/{team_id}", response_model=List[Dict])
def get_team_performance(
    team_id: int,
    service: MerchantAnalyticsService = Depends(get_merchant_analytics_service),
):
    """
    Get performance metrics for a team.
    """
    return service.get_team_performance(team_id)


@router.get("/actionable-alerts", response_model=List[str])
async def get_actionable_alerts(
    user: ShopifyUser = Depends(get_current_user),
    service: MerchantAnalyticsService = Depends(get_merchant_analytics_service),
):
    """
    Get actionable alerts for the current user.
    """
    return await service.check_for_actionable_alerts(user)


@router.post("/generate-seo-suggestions", response_model=str)
async def generate_seo_suggestions(
    analysis_results: Dict[str, Any],
    service: MerchantAnalyticsService = Depends(get_merchant_analytics_service),
):
    """
    Generate AI-powered suggestions to improve SEO based on analysis results.
    """
    return await service.generate_seo_improvement_suggestions(analysis_results)
