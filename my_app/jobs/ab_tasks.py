import asyncio
import logging
from celery import shared_task
from celery.utils.log import get_task_logger
from sqlalchemy.orm import Session
from redis import Redis, RedisError

from ..database import SessionLocal
from ..services.ab_testing_service import ABTestingService
from ..models.ab_test import ABTest, ABTestStatus
from ..models.user import ShopifyUser

# Use Celery's logger for tasks
logger = get_task_logger(__name__)
logging.basicConfig(level=logging.INFO)

# --- Task Configuration ---
LOCK_ID = "lock:process_all_ab_tests"
# Lock timeout: 10 minutes. Prevents a lock from being held indefinitely if a worker crashes.
LOCK_EXPIRE_SECONDS = 60 * 10
# DB query batch size for memory efficiency
DB_BATCH_SIZE = 100


async def _process_single_test_async(db: Session, test: ABTest, user: ShopifyUser):
    """
    Asynchronously processes a single A/B test to check for a winner or rotate variants.
    A dedicated ABTestingService is created here to ensure session safety.
    """
    ab_testing_service = ABTestingService(db)
    try:
        logger.info(f"Processing A/B test ID: {test.id} for user: {user.shop_domain}")
        await ab_testing_service.check_and_declare_winner(test.id, user)
    except Exception as e:
        logger.error(f"Failed to process A/B test {test.id}: {e}", exc_info=True)
        # Re-raise the exception so asyncio.gather can capture it
        raise


async def _run_all_tests_async():
    """
    Gathers and runs all individual test processing tasks concurrently.
    Manages its own database session for async safety.
    """
    tasks = []
    with SessionLocal() as db:
        # 1. Flush metrics first (this is a synchronous operation)
        ab_testing_service = ABTestingService(db)
        logger.info("Flushing all pending A/B test metrics...")
        ab_testing_service.flush_metrics()
        logger.info("Metrics flushed successfully.")

        # 2. Efficiently query tests and users together using a JOIN
        logger.info("Fetching all running A/B tests...")
        query = (
            db.query(ABTest, ShopifyUser)
            .join(ShopifyUser, ABTest.user_id == ShopifyUser.id)
            .filter(ABTest.status == ABTestStatus.RUNNING)
        )

        # Use yield_per for memory efficiency with large numbers of tests
        for test, user in query.yield_per(DB_BATCH_SIZE):
            task = _process_single_test_async(db, test, user)
            tasks.append(task)

    if not tasks:
        logger.info("No running A/B tests to process.")
        return

    logger.info(f"Found {len(tasks)} running A/B tests to process concurrently.")
    # Run all tasks concurrently, capturing results and exceptions
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Log failures
    failures = [res for res in results if isinstance(res, Exception)]
    if failures:
        logger.error(
            f"{len(failures)} out of {len(tasks)} test-processing tasks failed."
        )
    else:
        logger.info(f"All {len(tasks)} test-processing tasks completed successfully.")


@shared_task(name="jobs.process_all_ab_tests")
def process_ab_tests():
    """
    Celery task to process all running A/B tests.
    - Redis lock logic is disabled.
    - Flushes metrics and processes all tests within a managed async event loop.
    """
    # try:
    #     redis_client: Redis = get_redis_client()
    # except RedisError as e:
    #     logger.critical(
    #         f"Could not connect to Redis. Aborting A/B test processing task. Error: {e}"
    #     )
    #     return

    # # Acquire lock to ensure only one instance of this task runs at a time
    # if not redis_client.set(LOCK_ID, "true", nx=True, ex=LOCK_EXPIRE_SECONDS):
    #     logger.warning(
    #         f"Could not acquire lock for '{LOCK_ID}'. Another task is likely running."
    #     )
    #     return

    logger.info("[Redis lock disabled] Starting A/B testing processing task.")
    try:
        # Run the main asynchronous logic
        asyncio.run(_run_all_tests_async())
        logger.info("Finished A/B testing processing task.")
    except Exception as e:
        logger.error(
            f"An unexpected error occurred during the main A/B test processing task: {e}",
            exc_info=True,
        )
    # finally:
    #     # Release the lock
    #     redis_client.delete(LOCK_ID)
    #     logger.info("A/B test processing lock released.")


@shared_task(name="jobs.schedule_ab_tests")
def schedule_ab_tests_task():
    """
    Celery task to schedule A/B tests.
    """
    with SessionLocal() as db:
        ab_testing_service = ABTestingService(db)
        ab_testing_service.schedule_ab_tests()
