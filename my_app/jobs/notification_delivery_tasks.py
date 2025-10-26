from celery import shared_task
from my_app.database import SessionLocal
from my_app.services.notification_service import NotificationService
from my_app.crud.user_crud import get_inactive_users
from my_app.schemas.notification import EventType


@shared_task(bind=True)
def send_inactive_user_notifications(self, days: int = 7):
    """
    Celery task to send notifications to users who have been inactive for a specified number of days.
    """
    with SessionLocal() as db:
        notification_service = NotificationService(db)
        inactive_users = get_inactive_users(db, days=days)
        for user in inactive_users:
            notification_service.notify_event(
                user_id=user.id, event_type=EventType.USER_INACTIVITY, data={}
            )
