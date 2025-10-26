import asyncio
import logging
from ..database import SessionLocal
from ..models.shop import ShopifyUser
from ..services.shop_service import ShopifyService
from ..crud import product_crud
from ..schemas.product import ProductCreate, ProductUpdate
from ..dependencies.config import settings
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def synchronize_products_for_user(user_id: int):
    """
    Synchronizes products from Shopify for a single user.
    """
    db = SessionLocal()
    try:
        user = db.query(ShopifyUser).filter(ShopifyUser.id == user_id).first()
        if not user:
            logger.error(f"User with ID {user_id} not found.")
            return

        logger.info(f"Starting product synchronization for shop: {user.shop_domain}")

        # The ShopifyService requires an OpenAI client, even if we don't use it here.
        # This is a design flaw in ShopifyService that should be addressed separately.
        # For now, we will create a dummy client.
        openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        service = ShopifyService(db, openai_client)

        try:
            shopify_products = await service.fetch_products(user)

            for shopify_product in shopify_products:
                db_product = product_crud.get_product(
                    db, product_id=shopify_product["id"]
                )

                if db_product:
                    # Update existing product
                    product_in = ProductUpdate(**shopify_product)
                    product_crud.update_product(
                        db, db_product=db_product, product_in=product_in
                    )
                    logger.debug(
                        f"Updated product: {shopify_product['title']} (ID: {shopify_product['id']})"
                    )
                else:
                    # Create new product
                    product_in = ProductCreate(**shopify_product)
                    product_crud.create_product(db, product=product_in)
                    logger.debug(
                        f"Created new product: {shopify_product['title']} (ID: {shopify_product['id']})"
                    )

            logger.info(
                f"Finished product synchronization for shop: {user.shop_domain}. Synchronized {len(shopify_products)} products."
            )

        except Exception as e:
            logger.error(
                f"An error occurred during product synchronization for shop {user.shop_domain}: {e}"
            )
        finally:
            await service.close()
    finally:
        db.close()


async def run_product_synchronization():
    """
    Runs the product synchronization for all users concurrently.
    This function is intended to be called by a scheduler.
    """
    logger.info("Starting product synchronization for all shops...")
    db = SessionLocal()
    try:
        user_ids = [user.id for user in db.query(ShopifyUser.id).all()]
        tasks = [synchronize_products_for_user(user_id) for user_id in user_ids]
        await asyncio.gather(*tasks)
    finally:
        db.close()
    logger.info("Product synchronization for all shops finished.")


if __name__ == "__main__":
    asyncio.run(run_product_synchronization())
