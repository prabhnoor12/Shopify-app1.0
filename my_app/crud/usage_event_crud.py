from sqlalchemy.orm import Session
from .. import schemas
from ..models.usage_event import UsageEvent
from typing import List


def create_usage_event(
    db: Session, usage_event: schemas.UsageEventCreate
) -> UsageEvent:
    db_usage_event = UsageEvent(**usage_event.model_dump())
    db.add(db_usage_event)
    db.commit()
    db.refresh(db_usage_event)
    return db_usage_event


def get_usage_events_by_user(
    db: Session, user_id: int, skip: int = 0, limit: int = 100
) -> List[UsageEvent]:
    return (
        db.query(UsageEvent)
        .filter(UsageEvent.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_usage_events_by_shop(
    db: Session, shop_id: int, skip: int = 0, limit: int = 100
) -> List[UsageEvent]:
    return (
        db.query(UsageEvent)
        .filter(UsageEvent.shop_id == shop_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
