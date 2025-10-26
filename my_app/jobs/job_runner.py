"""
This module initializes and configures the APScheduler for running background jobs.
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from my_app.jobs.autopromote_job import run_auto_promote_winner_job
from my_app.jobs.data_cleanup_job import run_daily_data_cleanup, run_weekly_data_cleanup, run_monthly_data_cleanup

# Configure logging
logging.basicConfig()
logging.getLogger("apscheduler").setLevel(logging.INFO)

# Initialize scheduler
scheduler = BackgroundScheduler()


def start_scheduler():
    """
    Starts the scheduler and adds the jobs.
    """
    # Add jobs to the scheduler
    # This job will run every hour
    scheduler.add_job(
        run_auto_promote_winner_job,
        "interval",
        hours=1,
        id="auto_promote_winner_job",
        replace_existing=True,
    )

    # Daily data cleanup - runs every day at 2 AM
    scheduler.add_job(
        run_daily_data_cleanup,
        "cron",
        hour=2,
        minute=0,
        id="daily_data_cleanup",
        replace_existing=True,
    )

    # Weekly data cleanup - runs every Sunday at 3 AM
    scheduler.add_job(
        run_weekly_data_cleanup,
        "cron",
        day_of_week=6,  # Sunday (0 = Monday, 6 = Sunday)
        hour=3,
        minute=0,
        id="weekly_data_cleanup",
        replace_existing=True,
    )

    # Monthly data cleanup - runs on the 1st of every month at 4 AM
    scheduler.add_job(
        run_monthly_data_cleanup,
        "cron",
        day=1,
        hour=4,
        minute=0,
        id="monthly_data_cleanup",
        replace_existing=True,
    )

    try:
        scheduler.start()
        logging.info("Scheduler started successfully.")
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logging.info("Scheduler shut down successfully.")


def stop_scheduler():
    """
    Stops the scheduler.
    """
    if scheduler.running:
        scheduler.shutdown()
        logging.info("Scheduler shut down successfully.")
