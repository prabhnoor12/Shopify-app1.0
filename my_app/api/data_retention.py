"""
API routes for data retention management and cleanup operations.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.data_retention_service import DataRetentionService
from typing import Dict

router = APIRouter(prefix="/retention", tags=["retention"])


@router.post("/cleanup/daily", response_model=Dict[str, int])
def run_daily_cleanup(db: Session = Depends(get_db)):
    """
    Manually trigger daily data cleanup operations.
    In production, this should be restricted to admin users only.
    """
    service = DataRetentionService(db)
    results = service.run_daily_cleanup()
    return results


@router.post("/cleanup/weekly", response_model=Dict[str, int])
def run_weekly_cleanup(db: Session = Depends(get_db)):
    """
    Manually trigger weekly data cleanup operations.
    In production, this should be restricted to admin users only.
    """
    service = DataRetentionService(db)
    results = service.run_weekly_cleanup()
    return results


@router.post("/cleanup/monthly", response_model=Dict[str, int])
def run_monthly_cleanup(db: Session = Depends(get_db)):
    """
    Manually trigger monthly data cleanup operations.
    In production, this should be restricted to admin users only.
    """
    service = DataRetentionService(db)
    results = service.run_monthly_cleanup()
    return results


@router.get("/stats", response_model=Dict[str, int])
def get_retention_stats(db: Session = Depends(get_db)):
    """
    Get statistics about data retention compliance.
    Shows counts of data by age categories.
    """
    service = DataRetentionService(db)
    stats = service.get_retention_stats()
    return stats


@router.delete("/sessions/expired")
def cleanup_expired_sessions(days_old: int = 30, db: Session = Depends(get_db)):
    """
    Manually clean up expired sessions older than specified days.
    """
    service = DataRetentionService(db)
    deleted_count = service.cleanup_expired_sessions(days_old)
    return {"message": f"Deleted {deleted_count} expired sessions"}


@router.delete("/usage/old")
def cleanup_old_usage_data(keep_years: int = 2, db: Session = Depends(get_db)):
    """
    Manually clean up old usage analytics data.
    """
    service = DataRetentionService(db)
    updated_count = service.cleanup_old_usage_data(keep_years)
    return {"message": f"Anonymized {updated_count} old usage records"}


@router.delete("/feedback/old")
def cleanup_old_feedback(keep_years: int = 3, db: Session = Depends(get_db)):
    """
    Manually clean up old user feedback.
    """
    service = DataRetentionService(db)
    deleted_count = service.cleanup_old_user_feedback(keep_years)
    return {"message": f"Deleted {deleted_count} old feedback records"}
