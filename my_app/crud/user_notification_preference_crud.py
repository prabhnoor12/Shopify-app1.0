from sqlalchemy.orm import Session
from ..models.user_notification_preference import UserNotificationPreference
from ..schemas.user_notification_preference import (
    UserNotificationPreferenceCreate,
    UserNotificationPreferenceUpdate,
)


def get_user_notification_preference(
    db: Session, user_id: int
) -> UserNotificationPreference:
    return (
        db.query(UserNotificationPreference)
        .filter(UserNotificationPreference.user_id == user_id)
        .first()
    )


def create_user_notification_preference(
    db: Session, user_id: int, preference: UserNotificationPreferenceCreate
) -> UserNotificationPreference:
    db_preference = UserNotificationPreference(
        user_id=user_id, **preference.model_dump()
    )
    db.add(db_preference)
    db.commit()
    db.refresh(db_preference)
    return db_preference


def update_user_notification_preference(
    db: Session, user_id: int, preference: UserNotificationPreferenceUpdate
) -> UserNotificationPreference:
    db_preference = get_user_notification_preference(db, user_id)
    if db_preference:
        update_data = preference.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_preference, key, value)
        db.commit()
        db.refresh(db_preference)
    return db_preference
