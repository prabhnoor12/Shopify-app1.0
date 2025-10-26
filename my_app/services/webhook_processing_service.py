import logging
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from ..crud.subscription_crud import subscription as crud_subscription
from ..crud.shop_crud import get_user_by_domain
from ..models.subscription import SubscriptionStatus
from ..schemas.subscription import SubscriptionUpdate
from ..services.ab_testing_service import ABTestingService

logger = logging.getLogger(__name__)


class WebhookProcessingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def handle_app_subscriptions_update(self, payload: dict):
        from ..jobs.webhook_tasks import process_app_subscriptions_update

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
        process_app_subscriptions_update.delay(payload)
        logger.info(
            f"Queued app/subscriptions/update webhook for charge ID {charge_id}."
        )
        return {"message": "Webhook received and queued for processing."}

    async def handle_app_uninstalled(self, payload: dict):
        shop_domain = payload.get("myshopify_domain")

        if not shop_domain:
            logger.error(
                f"Missing shop_domain in app/uninstalled webhook payload: {payload}"
            )
            return {
                "message": "Missing shop_domain in webhook payload.",
                "status_code": 400,
            }

        user_subscription = (
            await crud_subscription.get_active_subscription_by_shop_domain(
                self.db, shop_domain=shop_domain
            )
        )

        if user_subscription:
            if user_subscription.status != SubscriptionStatus.CANCELED:
                subscription_update = SubscriptionUpdate(
                    status=SubscriptionStatus.CANCELED, updated_at=datetime.utcnow()
                )
                await crud_subscription.update(
                    self.db, db_obj=user_subscription, obj_in=subscription_update
                )
                logger.info(f"Subscription for shop {shop_domain} marked as canceled.")
                return {
                    "message": f"Subscription for shop {shop_domain} marked as canceled."
                }
            else:
                logger.info(
                    f"Subscription for shop {shop_domain} already canceled. No update needed."
                )
                return {
                    "message": f"Subscription for shop {shop_domain} already canceled. No update needed."
                }
        else:
            logger.warning(
                f"No active subscription found for shop {shop_domain}. Webhook processed, but no update made."
            )
            return {
                "message": f"No active subscription found for shop {shop_domain}, webhook processed."
            }

    def handle_product_creation(self, payload: dict):
        product_id = payload.get("id")
        product_title = payload.get("title")
        logger.info(
            f"WebhookProcessingService: New product created: {product_title} (ID: {product_id})"
        )
        # Example: Add analytics, notifications, or DB logging here
        return {"message": "Product creation webhook processed successfully."}

    async def handle_order_creation(self, payload: dict, shop_domain: str):
        user = await get_user_by_domain(self.db, shop_domain=shop_domain)
        if not user:
            logger.warning(
                f"Shopify user not found for domain {shop_domain} in orders/create webhook."
            )
            return {
                "message": "Shopify user not found for this domain.",
                "status_code": 404,
            }

        ab_testing_service = ABTestingService(self.db)

        for line_item in payload.get("line_items", []):
            product_id = line_item.get("product_id")
            if product_id:
                ab_test = await self.db.execute(
                    ab_testing_service.ABTest.select().where(
                        ab_testing_service.ABTest.product_id == product_id,
                        ab_testing_service.ABTest.user_id == user.id,
                        ab_testing_service.ABTest.status == "running",
                    )
                )
                ab_test = ab_test.scalars().first()

                if ab_test and ab_test.active_variant_id:
                    await ab_testing_service.record_conversion(
                        ab_test.active_variant_id
                    )
                    logger.info(
                        f"Recorded conversion for A/B test {ab_test.id} variant {ab_test.active_variant_id}."
                    )

        logger.info("Order creation webhook processed successfully.")
        return {"message": "Order creation webhook processed successfully."}
