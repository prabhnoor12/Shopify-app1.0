import asyncio
import logging
import json
from datetime import datetime, timedelta
from sqlalchemy import func
from ..database import SessionLocal
from ..models.shop import ShopifyUser
from ..models.activity_log import ActivityLog
from ..models.report import Report

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def generate_daily_usage_report_for_user(user_id: int):
    """
    Generates a daily usage report for a single user.
    """
    db = SessionLocal()
    try:
        user = db.query(ShopifyUser).filter(ShopifyUser.id == user_id).first()
        if not user:
            logger.error(f"User with ID {user_id} not found.")
            return

        logger.info(f"Generating daily usage report for shop: {user.shop_domain}")

        yesterday = datetime.utcnow() - timedelta(days=1)
        start_of_day = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = yesterday.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        generations_count = (
            db.query(func.count(ActivityLog.id))
            .filter(
                ActivityLog.user_id == user_id,
                ActivityLog.action == "generate_description",
                ActivityLog.created_at >= start_of_day,
                ActivityLog.created_at <= end_of_day,
            )
            .scalar()
        )

        report_content = {
            "date": yesterday.date().isoformat(),
            "generations_count": generations_count,
        }

        report = Report(
            user_id=user_id,
            name=f"Daily Usage Report for {user.shop_domain} - {yesterday.date().isoformat()}",
            type="daily_usage",
            content=json.dumps(report_content),
        )
        db.add(report)
        db.commit()

        logger.info(
            f"Successfully generated daily usage report for shop: {user.shop_domain}"
        )

    except Exception as e:
        logger.error(
            f"An error occurred during daily usage report generation for shop {user.shop_domain}: {e}"
        )
        db.rollback()
    finally:
        db.close()


async def generate_top_products_report():
    """
    Generates a report of the top products with the most generated descriptions.
    """
    # This is a placeholder for the top products report generation logic.
    # It would involve querying the ActivityLog table and aggregating the results by product ID.
    logger.info("Generating top products report...")
    await asyncio.sleep(1)  # Simulate work
    logger.info("Top products report generated.")


async def generate_user_feedback_report():
    """
    Generates a report summarizing user feedback.
    """
    # This is a placeholder for the user feedback report generation logic.
    # It would involve querying the UserFeedback table and aggregating the results by status.
    logger.info("Generating user feedback report...")
    await asyncio.sleep(1)  # Simulate work
    logger.info("User feedback report generated.")


async def run_reporting_jobs():
    """
    Runs all reporting jobs concurrently.
    This function is intended to be called by a scheduler.
    """
    logger.info("Starting reporting jobs...")

    # Run user-specific reports concurrently
    db = SessionLocal()
    try:
        user_ids = [user.id for user in db.query(ShopifyUser.id).all()]
        daily_usage_tasks = [
            generate_daily_usage_report_for_user(user_id) for user_id in user_ids
        ]
        await asyncio.gather(*daily_usage_tasks)
    finally:
        db.close()

    # Run global reports
    await asyncio.gather(
        generate_top_products_report(),
        generate_user_feedback_report(),
    )

    logger.info("Reporting jobs finished.")


if __name__ == "__main__":
    asyncio.run(run_reporting_jobs())
