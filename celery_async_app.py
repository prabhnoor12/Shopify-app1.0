from celery import Celery
from my_app.dependencies.config import settings
import asyncio


class AsyncCelery(Celery):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.patch_task()

    def patch_task(self):
        TaskBase = self.Task

        class ContextTask(TaskBase):
            def __call__(self, *args, **kwargs):
                return asyncio.run(self.run(*args, **kwargs))

        self.Task = ContextTask


celery_app = AsyncCelery(
    "shopify_app",
    broker=settings.REDIS_BROKER_URL,
    backend=settings.REDIS_BACKEND_URL,
    include=[
        "my_app.jobs.webhook_tasks",
        "my_app.jobs.ab_testing_tasks",
        "my_app.jobs.scheduling_tasks",
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
    },
)

# IMPORTANT: Ensure settings.REDIS_BROKER_URL and settings.REDIS_BACKEND_URL
# are defined in my_app/dependencies/config.py
