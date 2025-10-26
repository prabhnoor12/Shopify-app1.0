from ...celery_async_app import celery_app
from datetime import datetime
import logging

from ..database import AsyncSessionLocal
from ..crud import subscription as crud_subscription
from ..models.subscription import SubscriptionStatus
from ..schemas.subscription import SubscriptionUpdate

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
async def process_app_subscriptions_update(self, payload: dict):
    """
    Celery task to process app/subscriptions/update webhooks.
    """
    async with AsyncSessionLocal() as db:
        try:
            charge_id = payload.get("id")
            status = payload.get("status")

            if not charge_id or not status:
                logger.error(
                    f"Missing charge_id or status in app/subscriptions/update webhook payload: {payload}"
                )
                return {
                    "message": "Missing charge_id or status in webhook payload.",
                    "status_code": 400,
                }

            subscription = (
                await crud_subscription.get_subscription_by_shopify_charge_id(
                    db, shopify_charge_id=charge_id
                )
            )

            if not subscription:
                logger.warning(
                    f"Subscription with Shopify charge ID {charge_id} not found in our database. Webhook processed, but no update made."
                )
                return {"message": "Subscription not found, but webhook processed."}

            if status == "active":
                subscription_status = SubscriptionStatus.ACTIVE
            elif status == "cancelled" or status == "declined":
                subscription_status = SubscriptionStatus.CANCELED
            elif status == "pending":
                subscription_status = SubscriptionStatus.TRIALING
            else:
                logger.warning(
                    f"Unhandled Shopify subscription status '{status}' for charge ID {charge_id}."
                )
                return {"message": "Unhandled subscription status, webhook processed."}

            if subscription.status != subscription_status:
                subscription_update = SubscriptionUpdate(
                    status=subscription_status, updated_at=datetime.utcnow()
                )
                await crud_subscription.update_subscription(
                    db,
                    subscription_id=subscription.id,
                    subscription=subscription_update,
                )
                logger.info(f"Subscription {charge_id} updated to {status}.")
            else:
                logger.info(
                    f"Subscription {charge_id} status already {status}. No update needed."
                )

            return {"message": f"Subscription {charge_id} updated to {status}."}
        except Exception as exc:
            logger.error(f"Error processing app/subscriptions/update webhook: {exc}")
            await self.retry(exc=exc)
