from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from starlette.responses import RedirectResponse

from .. import schemas, crud
from ..database import get_db
from ..services.subscription_service import SubscriptionService
from ..dependencies import shopify
from ..models.subscription import SubscriptionStatus
from datetime import datetime
import requests  # Added requests import
from ..dependencies.config import get_settings  # Added get_settings

settings = get_settings()  # Initialize settings

router = APIRouter(
    prefix="/subscriptions",
    tags=["subscriptions"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=schemas.Subscription)
def create_subscription(
    subscription: schemas.SubscriptionCreate,
    shop_domain: str = Query(..., description="Shopify shop domain"),
    access_token: str = Query(..., description="Shopify access token"),
    db: Session = Depends(get_db),
):
    subscription_service = SubscriptionService(db)
    # The return_url will be handled by the frontend redirecting to this callback
    # For now, we pass a placeholder, but in a real app, this would be the app's base URL
    return subscription_service.create_subscription(
        user_id=subscription.user_id,
        shop_domain=shop_domain,
        access_token=access_token,
        return_url=f"https://{shop_domain}/admin/apps/{settings.SHOPIFY_APP_NAME}/auth/callback",  # This should be your app's callback URL
        subscription_create=subscription,
    )


@router.get("/activate-callback")
async def activate_subscription_callback(
    charge_id: int = Query(..., alias="charge_id"),
    shop: str = Query(..., alias="shop"),
    db: Session = Depends(get_db),
):
    # In a real application, you would retrieve the access_token for the shop from your database
    # For this example, we'll assume it's available or passed securely.
    # This is a critical security point: NEVER expose access tokens directly in URLs.
    # You should fetch the access_token from your database using the 'shop' domain.

    shop_user = crud.shop.get_user_by_domain(db, shop_domain=shop)
    if not shop_user:
        raise HTTPException(status_code=404, detail="Shop not found.")
    access_token = shop_user.access_token

    try:
        # Activate the recurring application charge on Shopify
        shopify.activate_recurring_application_charge(
            shop_domain=shop, access_token=access_token, charge_id=charge_id
        )

        # Update the subscription status in our database
        subscription = crud.subscription.get_subscription_by_shopify_charge_id(
            db, shopify_charge_id=charge_id
        )
        if subscription:
            subscription_update = schemas.SubscriptionUpdate(
                status=SubscriptionStatus.ACTIVE, updated_at=datetime.utcnow()
            )
            crud.subscription.update_subscription(
                db, subscription_id=subscription.id, subscription=subscription_update
            )

        # Redirect to a success page or the app dashboard
        return RedirectResponse(
            url=f"https://{shop}/admin/apps/{settings.SHOPIFY_APP_NAME}/dashboard?status=success"
        )

    except requests.exceptions.RequestException as e:
        print(f"Error activating Shopify recurring charge {charge_id}: {e}")
        raise HTTPException(
            status_code=503, detail=f"Shopify API error during activation: {e}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Subscription activation error: {e}"
        )


@router.get("/", response_model=List[schemas.Subscription])
def read_subscriptions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    subscriptions = crud.subscription.get_subscriptions(db, skip=skip, limit=limit)
    return subscriptions


@router.get("/{subscription_id}", response_model=schemas.Subscription)
def read_subscription(subscription_id: int, db: Session = Depends(get_db)):
    db_subscription = crud.subscription.get_subscription(
        db, subscription_id=subscription_id
    )
    if db_subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return db_subscription


@router.put("/{subscription_id}", response_model=schemas.Subscription)
def update_subscription(
    subscription_id: int,
    subscription: schemas.SubscriptionUpdate,
    shop_domain: str = Query(..., description="Shopify shop domain"),
    access_token: str = Query(..., description="Shopify access token"),
    db: Session = Depends(get_db),
):
    subscription_service = SubscriptionService(db)
    db_subscription = subscription_service.update_subscription(
        subscription_id=subscription_id,
        shop_domain=shop_domain,
        access_token=access_token,
        subscription_update=subscription,
    )
    if db_subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return db_subscription


@router.delete("/{subscription_id}", response_model=schemas.Subscription)
def cancel_subscription(
    subscription_id: int,
    shop_domain: str = Query(..., description="Shopify shop domain"),
    access_token: str = Query(..., description="Shopify access token"),
    db: Session = Depends(get_db),
):
    subscription_service = SubscriptionService(db)
    db_subscription = subscription_service.cancel_subscription(
        subscription_id=subscription_id,
        shop_domain=shop_domain,
        access_token=access_token,
    )
    if db_subscription is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return db_subscription


@router.get("/status/{user_id}")
def get_subscription_status(user_id: int, db: Session = Depends(get_db)):
    subscription_service = SubscriptionService(db)
    return subscription_service.get_subscription_status(user_id=user_id)
