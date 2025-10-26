from celery import Celery
from my_app.dependencies.config import settings

celery_app = Celery(
    "shopify_app",
    broker=settings.REDIS_BROKER_URL,
    backend=settings.REDIS_BACKEND_URL,
    include=[
        "my_app.jobs.ab_tasks",
        "my_app.jobs.audit_tasks",
        "my_app.jobs.autopromote_job",
        "my_app.jobs.cleanup_tasks",
        "my_app.jobs.data_synchronization_tasks",
        "my_app.jobs.notification_delivery_tasks",
        "my_app.jobs.reporting_tasks",
        "my_app.jobs.scheduling_tasks",
        "my_app.jobs.webhook_tasks",
        "my_app.jobs.seo_tasks",
        "my_app.jobs.performance_tasks",
    ],
)

# Optional: Configure Celery
celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "run-due-scheduled-tasks-every-minute": {
            "task": "my_app.jobs.scheduling_tasks.run_due_scheduled_tasks",
            "schedule": 60.0,  # Run every 60 seconds
        },
        "run-full-content-audit-daily": {
            "task": "my_app.jobs.audit_tasks.run_full_content_audit",
            "schedule": 86400.0,  # Run once every 24 hours
        },
        "run-seo-enhancements-weekly": {
            "task": "my_app.jobs.seo_tasks.run_seo_enhancements_for_all_products",
            "schedule": 604800.0,  # Run once every 7 days
        },
        "run-performance-analysis-monthly": {
            "task": "my_app.jobs.performance_tasks.run_performance_analysis_for_all_shops",
            "schedule": 2592000.0,  # Run once every 30 days
        },
    },
)

# IMPORTANT: Ensure settings.REDIS_BROKER_URL and settings.REDIS_BACKEND_URL
# are defined in my_app/dependencies/config.py
