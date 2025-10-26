import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models.user_feedback import UserFeedback
from ..models.learning_source import LearningSource
from ..models.activity_log import ActivityLog
from ..models.audit import AuditLog
from ..models.webhook_event import WebhookEvent
from ..models.session import Session as UserSession

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Cleanup Configuration ---
# Retention period for user feedback (in days)
USER_FEEDBACK_RETENTION_DAYS = 365
# Retention period for inactive learning sources (in days)
INACTIVE_LEARNING_SOURCE_RETENTION_DAYS = 90
# Retention period for activity logs (in days)
ACTIVITY_LOG_RETENTION_DAYS = 180
# Retention period for audit logs (in days)
AUDIT_LOG_RETENTION_DAYS = 365
# Retention period for webhook events (in days)
WEBHOOK_EVENT_RETENTION_DAYS = 30
# Retention period for expired user sessions (in days)
EXPIRED_SESSION_RETENTION_DAYS = 7


def cleanup_expired_user_feedback(db: Session):
    """
    Deletes user feedback records that are older than the retention period.
    """
    retention_threshold = datetime.utcnow() - timedelta(
        days=USER_FEEDBACK_RETENTION_DAYS
    )
    num_deleted = (
        db.query(UserFeedback)
        .filter(UserFeedback.created_at < retention_threshold)
        .delete()
    )
    if num_deleted > 0:
        logger.info(f"Deleted {num_deleted} expired user feedback records.")
    db.commit()


def cleanup_inactive_learning_sources(db: Session):
    """
    Deletes learning sources that have been inactive for longer than the retention period.
    """
    retention_threshold = datetime.utcnow() - timedelta(
        days=INACTIVE_LEARNING_SOURCE_RETENTION_DAYS
    )
    num_deleted = (
        db.query(LearningSource)
        .filter(
            LearningSource.is_active == False,
            LearningSource.updated_at < retention_threshold,
        )
        .delete()
    )
    if num_deleted > 0:
        logger.info(f"Deleted {num_deleted} inactive learning sources.")
    db.commit()


def cleanup_old_activity_logs(db: Session):
    """
    Deletes activity logs older than the retention period.
    """
    retention_threshold = datetime.utcnow() - timedelta(
        days=ACTIVITY_LOG_RETENTION_DAYS
    )
    num_deleted = (
        db.query(ActivityLog)
        .filter(ActivityLog.created_at < retention_threshold)
        .delete()
    )
    if num_deleted > 0:
        logger.info(f"Deleted {num_deleted} old activity logs.")
    db.commit()


def cleanup_old_audit_logs(db: Session):
    """
    Deletes audit logs older than the retention period.
    """
    retention_threshold = datetime.utcnow() - timedelta(days=AUDIT_LOG_RETENTION_DAYS)
    num_deleted = (
        db.query(AuditLog).filter(AuditLog.created_at < retention_threshold).delete()
    )
    if num_deleted > 0:
        logger.info(f"Deleted {num_deleted} old audit logs.")
    db.commit()


def cleanup_old_webhook_events(db: Session):
    """
    Deletes webhook events older than the retention period.
    """
    retention_threshold = datetime.utcnow() - timedelta(
        days=WEBHOOK_EVENT_RETENTION_DAYS
    )
    num_deleted = (
        db.query(WebhookEvent)
        .filter(WebhookEvent.created_at < retention_threshold)
        .delete()
    )
    if num_deleted > 0:
        logger.info(f"Deleted {num_deleted} old webhook events.")
    db.commit()


def cleanup_expired_sessions(db: Session):
    """
    Deletes expired user sessions.
    """
    retention_threshold = datetime.utcnow() - timedelta(
        days=EXPIRED_SESSION_RETENTION_DAYS
    )
    num_deleted = (
        db.query(UserSession)
        .filter(UserSession.expires_at < retention_threshold)
        .delete()
    )
    if num_deleted > 0:
        logger.info(f"Deleted {num_deleted} expired user sessions.")
    db.commit()


def run_cleanup_jobs():
    """
    Runs all cleanup jobs.
    This function is intended to be called by a scheduler (e.g., Celery Beat, cron).
    """
    logger.info("Starting cleanup jobs...")
    db = SessionLocal()
    try:
        cleanup_expired_user_feedback(db)
        cleanup_inactive_learning_sources(db)
        cleanup_old_activity_logs(db)
        cleanup_old_audit_logs(db)
        cleanup_old_webhook_events(db)
        cleanup_expired_sessions(db)
        logger.info("Cleanup jobs finished successfully.")
    except Exception as e:
        logger.error(f"An error occurred during cleanup jobs: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    run_cleanup_jobs()
