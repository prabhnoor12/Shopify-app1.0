import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from openai import OpenAI
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..database import get_db
from ..dependencies.auth import get_current_user
from ..models.shop import ShopifyUser
from ..services.shop_service import ShopifyService
from ..schemas.shop import (
    GenerateRequest,
    SaveRequest,
    BulkGenerateRequest,
    BulkSaveRequest,
    BulkGenerateResponse,
    GenerateFromImageRequest,
    GenerateFromUrlRequest,
    GenerateResponse,
    BulkSaveResponse,
    RegenerateVariantRequest,
    BenefitOrientedRequest,
    BenefitOrientedResponse,
    BulkFindReplaceRequest,
    BulkFindReplaceResponse,
)
from my_app.dependencies.config import settings

router = APIRouter(prefix="/api", tags=["products"])
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)


def get_openai_client() -> OpenAI:
    """Dependency that provides an OpenAI client instance."""
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def get_shopify_service(
    db: Session = Depends(get_db), openai_client: OpenAI = Depends(get_openai_client)
) -> ShopifyService:
    """Dependency that provides a ShopifyService instance."""
    return ShopifyService(db, openai_client)


@router.get("/products", response_model=List[Dict[str, Any]])
@limiter.limit("5/minute")
async def get_products(
    request: Request,
    user: ShopifyUser = Depends(get_current_user),
    service: ShopifyService = Depends(get_shopify_service),
) -> List[Dict[str, Any]]:
    """
    Fetch all products for a given shop domain.
    """
    logger.info("Received request to fetch products for shop: %s", user.shop_domain)
    products = service.fetch_products(user)
    logger.info(
        "Successfully fetched %d products for shop: %s", len(products), user.shop_domain
    )
    return products


@router.post("/generate-description-from-url", response_model=GenerateResponse)
@limiter.limit("5/minute")
async def generate_description_from_url(
    request: Request,
    generate_request: GenerateFromUrlRequest,
    user: ShopifyUser = Depends(get_current_user),
    service: ShopifyService = Depends(get_shopify_service),
) -> GenerateResponse:
    """
    Generate a product description from a URL by scraping it.
    """
    logger.info(
        "Received request to generate description from URL: %s", generate_request.url
    )
    response = service.generate_description_from_url(
        user=user, request=generate_request
    )
    logger.info("Successfully generated description from URL: %s", generate_request.url)
    return response


@router.post("/generate-description", response_model=Dict[str, str])
@limiter.limit("5/minute")
async def generate_description(
    request: Request,
    generate_request: GenerateRequest,
    user: ShopifyUser = Depends(get_current_user),
    service: ShopifyService = Depends(get_shopify_service),
) -> Dict[str, str]:
    """
    Generate a product description using OpenAI for a given product.
    """
    logger.info(
        "Received request to generate description for product: %s",
        generate_request.title,
    )
    description = service.generate_description(user=user, request=generate_request)
    logger.info(
        "Successfully generated description for product: %s", generate_request.title
    )
    return {"description": description}


@router.post("/generate-description-from-image", response_model=BulkGenerateResponse)
@limiter.limit("5/minute")
async def generate_description_from_image(
    request: Request,
    generate_request: GenerateFromImageRequest,
    user: ShopifyUser = Depends(get_current_user),
    service: ShopifyService = Depends(get_shopify_service),
) -> BulkGenerateResponse:
    """
    Generate a product description from an image URL.
    """
    logger.info(
        "Received request to generate description from image for user: %s",
        user.shop_domain,
    )
    response = service.generate_description_from_image(
        user=user, request=generate_request
    )
    logger.info(
        "Successfully generated description from image for user: %s", user.shop_domain
    )
    return response


@router.post("/save-description", response_model=Dict[str, str])
@limiter.limit("5/minute")
async def save_description(
    request: Request,
    save_request: SaveRequest,
    user: ShopifyUser = Depends(get_current_user),
    service: ShopifyService = Depends(get_shopify_service),
) -> Dict[str, str]:
    """
    Save a new product description to Shopify for a given product.
    """
    logger.info(
        "Received request to save description for product ID: %s",
        save_request.product_id,
    )
    service.save_description(user=user, request=save_request)
    logger.info(
        "Successfully saved description for product ID: %s", save_request.product_id
    )
    return {"message": "Product description updated successfully."}


@router.post("/bulk-generate-descriptions", response_model=BulkGenerateResponse)
@limiter.limit("5/minute")
async def bulk_generate_descriptions(
    request: Request,
    generate_request: BulkGenerateRequest,
    user: ShopifyUser = Depends(get_current_user),
    service: ShopifyService = Depends(get_shopify_service),
) -> BulkGenerateResponse:
    """
    Generate product descriptions in bulk.
    """
    logger.info(
        "Received request to generate descriptions in bulk for shop: %s",
        user.shop_domain,
    )
    response = service.bulk_generate_descriptions(user=user, request=generate_request)
    logger.info(
        "Successfully generated descriptions in bulk for shop: %s", user.shop_domain
    )
    return response


@router.post("/bulk-save-descriptions", response_model=BulkSaveResponse)
@limiter.limit("5/minute")
async def bulk_save_descriptions(
    request: Request,
    save_request: BulkSaveRequest,
    user: ShopifyUser = Depends(get_current_user),
    service: ShopifyService = Depends(get_shopify_service),
) -> BulkSaveResponse:
    """
    Save product descriptions in bulk.
    """
    logger.info(
        "Received request to save descriptions in bulk for shop: %s", user.shop_domain
    )
    response = service.bulk_save_descriptions(user=user, request=save_request)
    logger.info(
        "Successfully saved descriptions in bulk for shop: %s", user.shop_domain
    )
    return response


@router.post("/bulk-find-replace", response_model=BulkFindReplaceResponse)
@limiter.limit("1/minute")  # Limit to 1 per minute as this can be a long-running task
async def bulk_find_and_replace(
    request: Request,
    find_replace_request: BulkFindReplaceRequest,
    user: ShopifyUser = Depends(get_current_user),
    service: ShopifyService = Depends(get_shopify_service),
) -> BulkFindReplaceResponse:
    """
    Find and replace text across all or a subset of product descriptions.
    """
    logger.info("Received bulk find and replace request for shop: %s", user.shop_domain)
    response = service.bulk_find_and_replace(user=user, request=find_replace_request)
    logger.info("Completed bulk find and replace for shop: %s", user.shop_domain)
    return response


@router.post("/regenerate-variant", response_model=BulkGenerateResponse)
@limiter.limit("5/minute")
async def regenerate_variant(
    request: Request,
    regenerate_request: RegenerateVariantRequest,
    user: ShopifyUser = Depends(get_current_user),
    service: ShopifyService = Depends(get_shopify_service),
) -> BulkGenerateResponse:
    """
    Regenerate a single product description variant.
    """
    logger.info(
        "Received request to regenerate variant for product ID: %s",
        regenerate_request.product_id,
    )
    response = await service.regenerate_variant(user=user, request=regenerate_request)
    logger.info(
        "Successfully regenerated variant for product ID: %s",
        regenerate_request.product_id,
    )
    return response


@router.post("/transform-feature-to-benefit", response_model=BenefitOrientedResponse)
@limiter.limit(
    "10/minute"
)  # Allow a slightly higher limit for this interactive feature
async def transform_feature_to_benefit(
    request: Request,
    benefit_request: BenefitOrientedRequest,
    user: ShopifyUser = Depends(get_current_user),
    service: ShopifyService = Depends(get_shopify_service),
) -> BenefitOrientedResponse:
    """
    Transforms a product feature into a customer-centric benefit.
    """
    logger.info(
        "Received request to transform feature to benefit for user: %s",
        user.shop_domain,
    )
    response = service.transform_feature_to_benefit(user=user, request=benefit_request)
    logger.info(
        "Successfully transformed feature to benefit for user: %s", user.shop_domain
    )
    return response
