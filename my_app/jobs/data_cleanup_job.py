"""
Scheduled jobs for automated data cleanup and retention management.
"""

import logging
from my_app.database import get_db_session
from my_app.services.data_retention_service import DataRetentionService

logger = logging.getLogger(__name__)


def run_daily_data_cleanup():
    """
    Daily cleanup job - runs every day at 2 AM.
    Cleans up expired sessions and temporary data.
    """
    logger.info("Starting daily data cleanup job")

    try:
        db = next(get_db_session())
        service = DataRetentionService(db)

        results = service.run_daily_cleanup()
        logger.info(f"Daily cleanup completed successfully: {results}")

    except Exception as e:
        logger.error(f"Daily cleanup job failed: {e}")
    finally:
        db.close()


def run_weekly_data_cleanup():
    """
    Weekly cleanup job - runs every Sunday at 3 AM.
    Cleans up old user feedback and analytics data.
    """
    logger.info("Starting weekly data cleanup job")

    try:
        db = next(get_db_session())
        service = DataRetentionService(db)

        results = service.run_weekly_cleanup()
        logger.info(f"Weekly cleanup completed successfully: {results}")

    except Exception as e:
        logger.error(f"Weekly cleanup job failed: {e}")
    finally:
        db.close()


def run_monthly_data_cleanup():
    """
    Monthly cleanup job - runs on the 1st of every month at 4 AM.
    Processes old audit logs and performs retention audits.
    """
    logger.info("Starting monthly data cleanup job")

    try:
        db = next(get_db_session())
        service = DataRetentionService(db)

        results = service.run_monthly_cleanup()
        logger.info(f"Monthly cleanup completed successfully: {results}")

    except Exception as e:
        logger.error(f"Monthly cleanup job failed: {e}")
    finally:
        db.close()
