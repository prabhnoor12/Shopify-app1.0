import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from .. import schemas
from ..crud.subscription_crud import subscription as subscription_crud
from ..dependencies import shopify
from ..core.pricing_config import PRICING_PLANS
from .usage_service import UsageService
from ..dependencies.config import get_settings
from ..crud import plan as crud_plan
import datetime
import requests

settings = get_settings()
logger = logging.getLogger(__name__)  # Initialize logger


class SubscriptionService:
    def __init__(self, db: Session):
        self.db = db
        self.usage_service = UsageService(db)

    def get_insights(self, subscription, usage):
        """
        Get insights based on the user's subscription and usage data.
        :param subscription:
        :param usage:
        """
        insights = {}
        plan_details = PRICING_PLANS.get(subscription.plan.name, {})
        plan_features = plan_details.get("features", {})
        feature_access_percentage = plan_details.get("feature_access_percentage", 0)

        # Upgrade recommendations based on new pricing strategy
        if subscription.plan == "free":
            if usage.get("descriptions_generated_short", 0) >= plan_features.get(
                "descriptions_generated_short", 0
            ):
                insights["upgrade_recommendation"] = (
                    "You have used all your free short descriptions. Upgrade to a paid plan to generate more."
                )
            elif (
                usage.get("descriptions_generated_long", 0) > 0
            ):  # Long descriptions are not free
                insights["upgrade_recommendation"] = (
                    "Long descriptions are not available on the free plan. Upgrade to a paid plan."
                )
            # Check for other features after the first month free
            elif (
                usage.get("images_processed_sd", 0) > 0
                or usage.get("images_processed_hd", 0) > 0
            ) and plan_details.get("trial_days", 0) == 0:
                insights["upgrade_recommendation"] = (
                    "Your free trial for image processing has ended. Upgrade to a paid plan for continued access."
                )
        else:  # Paid plans (basic, advanced, enterprise)
            for feature, limit in plan_features.items():
                if limit != -1:  # If not unlimited
                    # Calculate effective limit based on feature_access_percentage
                    effective_limit = limit * (feature_access_percentage / 100)
                    if usage.get(feature, 0) >= effective_limit:
                        insights["upgrade_recommendation"] = (
                            f"You have reached your limit for {feature}. Upgrade your plan to get more."
                        )
                        break
                    elif usage.get(feature, 0) >= effective_limit * 0.8:
                        insights["upgrade_warning"] = (
                            f"You have used 80% or more of your {feature} limit. Consider upgrading."
                        )
                        break

        # Churn risk (simplified)
        if subscription.plan != "free":
            # Focus on core usage metrics for churn risk
            core_usage_metrics = [
                usage.get("descriptions_generated_short", 0),
                usage.get("descriptions_generated_long", 0),
                usage.get("images_processed_sd", 0),
                usage.get("images_processed_hd", 0),
            ]
            total_core_usage = sum(core_usage_metrics)

            if total_core_usage < 10:  # Arbitrary low usage threshold for core features
                insights["churn_risk"] = (
                    "User has very low activity in core features. At risk of churn."
                )

        # Power user insights
        if subscription.plan == "basic":
            power_user_threshold = plan_details.get(
                "power_user_threshold_descriptions", 0
            )
            total_descriptions = usage.get(
                "descriptions_generated_short", 0
            ) + usage.get("descriptions_generated_long", 0)
            if power_user_threshold > 0 and total_descriptions > power_user_threshold:
                insights["power_user"] = (
                    "This is a power user of the description generator. A good candidate for the Advanced or Enterprise plan."
                )

        return insights

    def create_subscription(
        self,
        user_id: int,
        shop_domain: str,
        access_token: str,
        return_url: str,
        subscription_create: schemas.SubscriptionCreate,
    ):
        existing_subscription = subscription_crud.get_subscription_by_user(
            self.db, user_id=user_id
        )
        if (
            existing_subscription
            and existing_subscription.status == schemas.SubscriptionStatus.ACTIVE
        ):
            logger.warning(f"User {user_id} already has an active subscription.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has an active subscription.",
            )

        # Fetch plan details from the database using plan_id
        db_plan = crud_plan.get_plan(self.db, plan_id=subscription_create.plan_id)
        if not db_plan:
            logger.error(
                f"Plan with ID {subscription_create.plan_id} not found for user {user_id}."
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plan with ID {subscription_create.plan_id} not found.",
            )

        plan_name = db_plan.name  # Get the plan name (e.g., "basic", "advanced")
        plan_details = PRICING_PLANS.get(plan_name)

        if not plan_details:
            logger.error(
                f"Invalid plan name '{plan_name}' in PRICING_PLANS for user {user_id}."
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid plan name in PRICING_PLANS: {plan_name}",
            )

        # Create recurring application charge with Shopify
        try:
            charge_response = shopify.create_recurring_application_charge(
                shop_domain=shop_domain,
                access_token=access_token,
                name=plan_details["name"],
                price=plan_details["price"],
                return_url=return_url,
                test=settings.SHOPIFY_BILLING_TEST_MODE,  # Use configurable test mode
            )
            confirmation_url = charge_response["recurring_application_charge"][
                "confirmation_url"
            ]
            shopify_charge_id = charge_response["recurring_application_charge"]["id"]

            subscription_create.shopify_charge_id = shopify_charge_id
            subscription_create.confirmation_url = confirmation_url
            subscription_create.status = (
                "pending"  # Set to pending until activated by user
            )

            return subscription_crud.create(self.db, obj_in=subscription_create)

        except requests.exceptions.RequestException as e:
            logger.error(
                f"Shopify API error creating recurring charge for user {user_id}: {e}"
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Shopify API error: {e}",
            )

    def update_subscription(
        self,
        subscription_id: int,
        shop_domain: str,
        access_token: str,
        return_url: str,
        subscription_update: schemas.SubscriptionUpdate,
    ):
        subscription = subscription_crud.get_subscription(
            self.db, subscription_id=subscription_id
        )
        if not subscription:
            logger.error(f"Subscription {subscription_id} not found for update.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found."
            )

        # Handle plan changes
        if (
            subscription_update.plan_id
            and subscription_update.plan_id != subscription.plan_id
        ):
            # Fetch old and new plan details
            old_db_plan = crud_plan.get_plan(self.db, plan_id=subscription.plan_id)
            new_db_plan = crud_plan.get_plan(
                self.db, plan_id=subscription_update.plan_id
            )

            if not old_db_plan or not new_db_plan:
                logger.error(
                    f"Old plan (ID: {subscription.plan_id}) or New plan (ID: {subscription_update.plan_id}) not found for subscription {subscription_id}."
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid plan ID provided.",
                )

            old_plan_details = PRICING_PLANS.get(old_db_plan.name)
            new_plan_details = PRICING_PLANS.get(new_db_plan.name)

            if not old_plan_details or not new_plan_details:
                logger.error(
                    f"Plan details not found in PRICING_PLANS for old plan '{old_db_plan.name}' or new plan '{new_db_plan.name}'."
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid plan configuration.",
                )

            # Create a new recurring application charge for the new plan
            try:
                charge_response = shopify.create_recurring_application_charge(
                    shop_domain=shop_domain,
                    access_token=access_token,
                    name=new_plan_details["name"],
                    price=new_plan_details["price"],
                    return_url=return_url,  # This should be the callback URL after user approves
                    test=settings.SHOPIFY_BILLING_TEST_MODE,
                )
                new_confirmation_url = charge_response["recurring_application_charge"][
                    "confirmation_url"
                ]
                new_shopify_charge_id = charge_response["recurring_application_charge"][
                    "id"
                ]

                # Update the existing subscription record with the new charge details and pending status
                # The old charge will be cancelled via webhook once the new one is activated.
                subscription_update.shopify_charge_id = new_shopify_charge_id
                subscription_update.confirmation_url = new_confirmation_url
                subscription_update.status = (
                    schemas.SubscriptionStatus.PENDING
                )  # Set to pending until activated by user

                updated_subscription = subscription_crud.update(
                    self.db,
                    db_obj=subscription,
                    obj_in=subscription_update,
                )
                # Return the confirmation URL for the frontend to redirect the user
                return {
                    "confirmation_url": new_confirmation_url,
                    "subscription": updated_subscription,
                }

            except requests.exceptions.RequestException as e:
                logger.error(
                    f"Shopify API error creating new recurring charge for plan change (sub {subscription_id}): {e}"
                )
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Shopify API error during plan change: {e}",
                )

        # If the status is being updated to canceled (and not part of a plan change), cancel on Shopify as well
        if (
            subscription_update.status == schemas.SubscriptionStatus.CANCELED
            and subscription.shopify_charge_id
        ):
            try:
                shopify.cancel_recurring_application_charge(
                    shop_domain=shop_domain,
                    access_token=access_token,
                    charge_id=subscription.shopify_charge_id,
                )
            except requests.exceptions.RequestException as e:
                logger.error(
                    f"Error canceling Shopify recurring charge {subscription.shopify_charge_id} for subscription {subscription_id}: {e}"
                )
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Shopify API error during cancellation: {e}",
                )

        # If no plan change and not a cancellation, just update the local record
        return subscription_crud.update(
            self.db, db_obj=subscription, obj_in=subscription_update
        )

    def cancel_subscription(
        self, subscription_id: int, shop_domain: str, access_token: str
    ):
        subscription = subscription_crud.get_subscription(
            self.db, subscription_id=subscription_id
        )
        if not subscription:
            logger.error(f"Subscription {subscription_id} not found for cancellation.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found."
            )

        if subscription.shopify_charge_id:
            try:
                shopify.cancel_recurring_application_charge(
                    shop_domain=shop_domain,
                    access_token=access_token,
                    charge_id=subscription.shopify_charge_id,
                )
            except requests.exceptions.RequestException as e:
                logger.error(
                    f"Error canceling Shopify recurring charge {subscription.shopify_charge_id} for subscription {subscription_id}: {e}"
                )
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Shopify API error during cancellation: {e}",
                )

        # Set the status to 'canceled' in our database
        subscription_update = schemas.SubscriptionUpdate(
            status=schemas.SubscriptionStatus.CANCELED,
            updated_at=datetime.datetime.utcnow(),
        )
        return subscription_crud.update(
            self.db, db_obj=subscription, obj_in=subscription_update
        )

    def get_subscription_status(self, user_id: int) -> dict:
        subscription = subscription_crud.get_subscription_by_user(
            self.db, user_id=user_id
        )
        if not subscription:
            return {"status": "no_subscription", "plan": "none"}

        plan_details = PRICING_PLANS.get(subscription.plan.name, {})
        return {
            "status": subscription.status.value,
            "plan": subscription.plan.name,  # Return the plan name string
            "plan_name": plan_details.get("name", "Unknown Plan"),
            "trial_ends_at": subscription.trial_ends_at,
            "current_billing_period_starts_at": subscription.current_billing_period_starts_at,
            "current_billing_period_ends_at": subscription.current_billing_period_ends_at,
            "shopify_charge_id": subscription.shopify_charge_id,
            "confirmation_url": subscription.confirmation_url,
        }
