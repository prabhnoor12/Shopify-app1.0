import hmac
import hashlib
import json
import logging
from typing import Dict
from fastapi import APIRouter, Header, HTTPException, Request
from ..services.webhook_processing_service import WebhookProcessingService
from fastapi import Depends
from sqlalchemy.orm import Session
from ..database import get_db

from ..dependencies.config import get_settings

logger = logging.getLogger(__name__)  # Initialize logger
settings = get_settings()

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
WEBHOOK_SECRET = settings.SHOPIFY_WEBHOOK_SECRET  # Use settings for webhook secret


async def verify_shopify_webhook(
    request: Request, x_shopify_hmac_sha256: str = Header(...)
):
    """
    Verifies the HMAC signature from Shopify's webhook header.
    """
    if not WEBHOOK_SECRET:
        logger.error("Webhook secret not configured.")
        raise HTTPException(status_code=500, detail="Webhook secret not configured.")

    request_body = await request.body()
    digest = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"), request_body, hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(digest, x_shopify_hmac_sha256):
        logger.warning("Webhook signature verification failed.")
        raise HTTPException(
            status_code=403, detail="Webhook signature verification failed."
        )
    return request_body  # Return the body for further processing


@router.post("/shopify/app_subscriptions/update")
async def handle_app_subscriptions_update(
    request_body: bytes = Depends(verify_shopify_webhook), db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Handles app/subscriptions/update webhook from Shopify.
    Updates the subscription status in our database.
    """
    try:
        payload = json.loads(request_body.decode("utf-8"))
        service = WebhookProcessingService(db)
        result = service.handle_app_subscriptions_update(payload)

        if "status_code" in result and result["status_code"] != 200:
            raise HTTPException(
                status_code=result["status_code"], detail=result["message"]
            )

        return {"message": result["message"]}
    except json.JSONDecodeError:
        logger.error(
            f"Invalid JSON payload for app/subscriptions/update webhook: {request_body.decode('utf-8')}"
        )
        raise HTTPException(status_code=400, detail="Invalid JSON payload.")
    except Exception as e:
        logger.exception(f"Webhook processing error for app/subscriptions/update: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {e}")


@router.post("/shopify/app_uninstalled")
async def handle_app_uninstalled(
    request_body: bytes = Depends(verify_shopify_webhook), db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Handles app/uninstalled webhook from Shopify.
    Marks the user's subscription as canceled.
    """
    try:
        payload = json.loads(request_body.decode("utf-8"))
        service = WebhookProcessingService(db)
        result = service.handle_app_uninstalled(payload)

        if "status_code" in result and result["status_code"] != 200:
            raise HTTPException(
                status_code=result["status_code"], detail=result["message"]
            )

        return {"message": result["message"]}
    except json.JSONDecodeError:
        logger.error(
            f"Invalid JSON payload for app/uninstalled webhook: {request_body.decode('utf-8')}"
        )
        raise HTTPException(status_code=400, detail="Invalid JSON payload.")
    except Exception as e:
        logger.exception(f"Webhook processing error for app/uninstalled: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {e}")


@router.post("/products/create")
async def handle_product_creation(
    request_body: bytes = Depends(verify_shopify_webhook), db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Handles a product creation webhook from Shopify.
    """
    try:
        payload = json.loads(request_body.decode("utf-8"))
        service = WebhookProcessingService(db)
        result = service.handle_product_creation(payload)

        if "status_code" in result and result["status_code"] != 200:
            raise HTTPException(
                status_code=result["status_code"], detail=result["message"]
            )

        return {"message": result["message"]}
    except json.JSONDecodeError:
        logger.error(
            f"Invalid JSON payload for products/create webhook: {request_body.decode('utf-8')}"
        )
        raise HTTPException(status_code=400, detail="Invalid JSON payload.")
    except Exception as e:
        logger.exception(f"Webhook processing error for products/create: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {e}")


@router.post("/orders/create")
async def handle_order_creation(
    request_body: bytes = Depends(verify_shopify_webhook),
    x_shopify_shop_domain: str = Header(...),
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """
    Handles an order creation webhook from Shopify to record conversions for A/B tests.
    """
    try:
        payload = json.loads(request_body.decode("utf-8"))
        service = WebhookProcessingService(db)
        result = service.handle_order_creation(payload, x_shopify_shop_domain)

        if "status_code" in result and result["status_code"] != 200:
            raise HTTPException(
                status_code=result["status_code"], detail=result["message"]
            )

        return {"message": result["message"]}
    except json.JSONDecodeError:
        logger.error(
            f"Invalid JSON payload for orders/create webhook: {request_body.decode('utf-8')}"
        )
        raise HTTPException(status_code=400, detail="Invalid JSON payload.")
    except Exception as e:
        logger.exception(f"Webhook processing error for orders/create: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {e}")
