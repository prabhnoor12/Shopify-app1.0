import logging
import time
from functools import wraps
from sqlalchemy.orm import Session
from my_app import crud, schemas
from my_app.crud import subscription_crud as crud_subscription
from my_app.crud import usage_event_crud as crud_usage_event
from my_app.crud import shop_crud as crud_shop
from my_app.core.pricing_config import PRICING_PLANS, USAGE_CHARGE_RATES
from my_app.dependencies.shopify import get_shopify_client
from typing import Dict, Any, Optional
import requests

logger = logging.getLogger(__name__)  # Initialize logger


# Simple retry decorator for API calls
def retry(tries=3, delay=1, backoff=2):
    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except requests.exceptions.RequestException as e:
                    logger.warning(
                        f"{f.__name__} failed, retrying in {mdelay} seconds... ({e})"
                    )
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)  # Last attempt

        return f_retry

    return deco_retry


class UsageService:
    def __init__(self, db: Session):
        self.db = db

    @retry(tries=3, delay=2)  # Apply retry to record_usage
    def record_usage(
        self,
        user_id: int,
        shop_domain: str,
        access_token: str,
        subscription_plan: str,
        feature_name: str,
        quantity: int = 1,
        team_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        # Get or create usage record
        db_usage = crud.usage.get_usage_record(
            self.db, user_id=user_id, team_id=team_id
        )
        if not db_usage:
            usage_create = schemas.UsageCreate(user_id=user_id, team_id=team_id)
            db_usage = crud.usage.create_usage_record(self.db, usage_create)

        # Get current usage and calculate new usage
        current_usage_val = getattr(db_usage, feature_name, 0)
        new_usage_val = current_usage_val + quantity

        # Update specific feature usage
        usage_update_data = {feature_name: new_usage_val}
        crud.usage.update_usage_record(
            self.db,
            db_usage=db_usage,
            usage_in=schemas.UsageUpdate(**usage_update_data),
        )

        # Retrieve shop_id for UsageEvent
        shop_user = crud_shop.get_user_by_domain(self.db, shop_domain=shop_domain)
        if not shop_user:
            logger.error(
                f"Shop user not found for domain {shop_domain}. Cannot record UsageEvent."
            )
            return
        shop_id = shop_user.id

        # Create a UsageEvent record for detailed context
        usage_event_create = schemas.UsageEventCreate(
            user_id=user_id,
            shop_id=shop_id,
            feature_name=feature_name,
            quantity=quantity,
            context=context,
        )
        crud_usage_event.create_usage_event(self.db, usage_event=usage_event_create)

        # Handle billing for descriptions_generated_short and descriptions_generated_long
        if feature_name.startswith("descriptions_generated_"):
            plan_details = PRICING_PLANS.get(subscription_plan)
            if not plan_details:
                logger.error(
                    f"Invalid subscription plan '{subscription_plan}' for user {user_id}. Cannot process usage charge."
                )
                return

            free_limit = plan_details["features"].get(feature_name, 0)

            # Only charge if usage exceeds free limit and plan is not free
            if subscription_plan != "free" and new_usage_val > free_limit:
                charge_price = USAGE_CHARGE_RATES.get(feature_name, 0.0)
                if charge_price > 0:
                    # Fetch the user's active subscription to get the recurring_charge_id
                    active_subscription = crud_subscription.get_active_subscription_by_user_and_shop_domain(
                        self.db, user_id=user_id, shop_domain=shop_domain
                    )
                    if (
                        not active_subscription
                        or not active_subscription.shopify_charge_id
                    ):
                        logger.error(
                            f"No active subscription or shopify_charge_id found for user {user_id} and shop {shop_domain}. Cannot create usage charge."
                        )
                        return
                    recurring_charge_id = active_subscription.shopify_charge_id

                    try:
                        # Get an instance of the Shopify client
                        shopify_client = get_shopify_client(
                            shop_domain=shop_domain, access_token=access_token
                        )

                        # Call the method on the client instance
                        shopify_client.create_usage_charge(
                            recurring_charge_id=recurring_charge_id,
                            description=f"{feature_name} usage",
                            price=charge_price * quantity,
                            quantity=quantity,
                        )
                    except requests.exceptions.RequestException as e:
                        # The client now handles logging, but we can keep this for context
                        logger.error(
                            f"Usage charge creation failed for user {user_id}, feature {feature_name}: {e}"
                        )
                        raise  # Re-raise to allow retry decorator to catch it

    def get_user_usage(self, user_id: int) -> Dict[str, Any]:
        return crud.usage.get_total_usage_by_user(self.db, user_id=user_id)

    def get_team_usage(self, team_id: int) -> Dict[str, Any]:
        return crud.usage.get_total_usage_by_team(self.db, team_id=team_id)
