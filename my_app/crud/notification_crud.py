from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas


def create_notification(
    db: Session, notification: schemas.NotificationCreate
) -> models.Notification:
    db_notification = models.Notification(**notification.dict())
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification


def get_notifications_by_user(
    db: Session, user_id: int, skip: int = 0, limit: int = 100
) -> List[models.Notification]:
    return (
        db.query(models.Notification)
        .filter(models.Notification.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def mark_notification_as_read(
    db: Session, notification_id: int
) -> Optional[models.Notification]:
    db_notification = (
        db.query(models.Notification)
        .filter(models.Notification.id == notification_id)
        .first()
    )
    if db_notification:
        db_notification.is_read = True
        db.commit()
        db.refresh(db_notification)
    return db_notification
