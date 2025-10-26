from sqlalchemy.orm import Session
from ..models.usage import Usage
from .. import schemas
from typing import Dict, Any, Optional


def get_usage_record(
    db: Session, user_id: int, team_id: Optional[int] = None
) -> Optional[Usage]:
    """
    Retrieves the current usage record for a user, optionally within a team.
    For simplicity, we'll assume one active usage record per user (or team).
    """
    query = db.query(Usage).filter(Usage.user_id == user_id)
    if team_id:
        query = query.filter(Usage.team_id == team_id)
    return query.first()


def create_usage_record(db: Session, usage_in: schemas.UsageCreate) -> Usage:
    db_usage = Usage(**usage_in.model_dump())
    db.add(db_usage)
    db.commit()
    db.refresh(db_usage)
    return db_usage


def update_usage_record(
    db: Session, db_usage: Usage, usage_in: schemas.UsageUpdate
) -> Usage:
    for field, value in usage_in.model_dump(exclude_unset=True).items():
        setattr(db_usage, field, getattr(db_usage, field) + value)  # Increment usage
    db.add(db_usage)
    db.commit()
    db.refresh(db_usage)
    return db_usage


def get_total_usage_by_user(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Gets the total usage for all metrics for a given user.
    """
    usage_record = get_usage_record(db, user_id)
    if usage_record:
        return {
            "descriptions_generated_short": usage_record.descriptions_generated_short,
            "descriptions_generated_long": usage_record.descriptions_generated_long,
            "images_processed_sd": usage_record.images_processed_sd,
            "images_processed_hd": usage_record.images_processed_hd,
            "brand_voices_created": usage_record.brand_voices_created,
            "brand_voice_edited": usage_record.brand_voice_edited,
            "analytics_reports_generated": usage_record.analytics_reports_generated,
            "api_calls_made": usage_record.api_calls_made,
            "storage_used_mb": usage_record.storage_used_mb,
        }
    return {
        "descriptions_generated_short": 0,
        "descriptions_generated_long": 0,
        "images_processed_sd": 0,
        "images_processed_hd": 0,
        "brand_voices_created": 0,
        "brand_voice_edited": 0,
        "analytics_reports_generated": 0,
        "api_calls_made": 0,
        "storage_used_mb": 0,
    }


def get_total_usage_by_team(db: Session, team_id: int) -> Dict[str, Any]:
    """
    Gets the total usage for all metrics for a given team by summing across all users in the team.
    """
    team_usage_records = db.query(Usage).filter(Usage.team_id == team_id).all()

    total_usage = {
        "descriptions_generated_short": 0,
        "descriptions_generated_long": 0,
        "images_processed_sd": 0,
        "images_processed_hd": 0,
        "brand_voices_created": 0,
        "brand_voice_edited": 0,
        "analytics_reports_generated": 0,
        "api_calls_made": 0,
        "storage_used_mb": 0,
    }

    for record in team_usage_records:
        total_usage["descriptions_generated_short"] += (
            record.descriptions_generated_short
        )
        total_usage["descriptions_generated_long"] += record.descriptions_generated_long
        total_usage["images_processed_sd"] += record.images_processed_sd
        total_usage["images_processed_hd"] += record.images_processed_hd
        total_usage["brand_voices_created"] += record.brand_voices_created
        total_usage["brand_voice_edited"] += record.brand_voice_edited
        total_usage["analytics_reports_generated"] += record.analytics_reports_generated
        total_usage["api_calls_made"] += record.api_calls_made
        total_usage["storage_used_mb"] += record.storage_used_mb

    return total_usage
