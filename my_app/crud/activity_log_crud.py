from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas


def create_activity_log(
    db: Session, activity_log: schemas.ActivityLogCreate
) -> models.ActivityLog:
    db_activity_log = models.ActivityLog(**activity_log.dict())
    db.add(db_activity_log)
    db.commit()
    db.refresh(db_activity_log)
    return db_activity_log


def get_activity_logs_by_team(
    db: Session, team_id: int, skip: int = 0, limit: int = 100
) -> List[models.ActivityLog]:
    return (
        db.query(models.ActivityLog)
        .filter(models.ActivityLog.team_id == team_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
