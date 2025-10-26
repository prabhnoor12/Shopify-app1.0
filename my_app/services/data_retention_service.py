"""
Data retention and cleanup service for GDPR compliance.
Handles automated deletion of expired data according to retention policies.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class DataRetentionService:
    """
    Service for managing data retention and automated cleanup operations.
    """

    def __init__(self, db: Session):
        self.db = db

    def cleanup_expired_sessions(self, days_old: int = 30) -> int:
        """
        Delete sessions older than specified days.

        Args:
            days_old: Number of days after expiration to delete

        Returns:
            Number of sessions deleted
        """
        try:
            from ..models.session import Session
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)

            # Delete sessions that are both expired and older than cutoff
            deleted_count = (
                self.db.query(Session)
                .filter(Session.expires_at < cutoff_date)
                .delete()
            )

            self.db.commit()
            logger.info(f"Deleted {deleted_count} expired sessions older than {days_old} days")
            return deleted_count

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cleaning up expired sessions: {e}")
            return 0

    def cleanup_old_audit_logs(self, keep_years: int = 7) -> int:
        """
        Move or delete audit logs older than specified years.
        For compliance, we keep 7 years but may archive older logs.

        Args:
            keep_years: Number of years to keep audit logs

        Returns:
            Number of audit logs processed
        """
        try:
            from ..models.audit import AuditLog
            cutoff_date = datetime.utcnow() - timedelta(days=keep_years * 365)

            # For now, we'll just count - in production you might archive to separate storage
            old_logs_count = (
                self.db.query(AuditLog)
                .filter(AuditLog.created_at < cutoff_date)
                .count()
            )

            # TODO: Implement archiving to long-term storage instead of deletion
            # For compliance, we should archive rather than delete
            logger.info(f"Found {old_logs_count} audit logs older than {keep_years} years")
            return old_logs_count

        except Exception as e:
            logger.error(f"Error processing old audit logs: {e}")
            return 0

    def cleanup_old_usage_data(self, keep_years: int = 2) -> int:
        """
        Clean up usage analytics data older than specified years.

        Args:
            keep_years: Number of years to keep usage data

        Returns:
            Number of usage records deleted
        """
        try:
            from ..models.usage import Usage
            cutoff_date = datetime.utcnow() - timedelta(days=keep_years * 365)

            # Update usage records to remove old data
            # This is a soft delete approach - anonymize rather than remove
            updated_count = (
                self.db.query(Usage)
                .filter(Usage.last_reset < cutoff_date)
                .update({
                    "total_requests": 0,
                    "monthly_requests": 0,
                    "last_reset": datetime.utcnow()
                })
            )

            self.db.commit()
            logger.info(f"Anonymized {updated_count} old usage records")
            return updated_count

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cleaning up old usage data: {e}")
            return 0

    def cleanup_old_user_feedback(self, keep_years: int = 3) -> int:
        """
        Clean up user feedback older than specified years.

        Args:
            keep_years: Number of years to keep feedback

        Returns:
            Number of feedback records deleted
        """
        try:
            from ..models.user_feedback import UserFeedback
            cutoff_date = datetime.utcnow() - timedelta(days=keep_years * 365)

            deleted_count = (
                self.db.query(UserFeedback)
                .filter(UserFeedback.created_at < cutoff_date)
                .delete()
            )

            self.db.commit()
            logger.info(f"Deleted {deleted_count} user feedback records older than {keep_years} years")
            return deleted_count

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cleaning up old user feedback: {e}")
            return 0

    def run_daily_cleanup(self) -> Dict[str, int]:
        """
        Run all daily cleanup operations.

        Returns:
            Dictionary with cleanup results
        """
        logger.info("Starting daily data cleanup")

        results = {
            "expired_sessions": self.cleanup_expired_sessions(),
            "old_usage_data": self.cleanup_old_usage_data(),
        }

        logger.info(f"Daily cleanup completed: {results}")
        return results

    def run_weekly_cleanup(self) -> Dict[str, int]:
        """
        Run all weekly cleanup operations.

        Returns:
            Dictionary with cleanup results
        """
        logger.info("Starting weekly data cleanup")

        results = {
            "old_user_feedback": self.cleanup_old_user_feedback(),
        }

        logger.info(f"Weekly cleanup completed: {results}")
        return results

    def run_monthly_cleanup(self) -> Dict[str, int]:
        """
        Run all monthly cleanup operations.

        Returns:
            Dictionary with cleanup results
        """
        logger.info("Starting monthly data cleanup")

        results = {
            "old_audit_logs": self.cleanup_old_audit_logs(),
        }

        logger.info(f"Monthly cleanup completed: {results}")
        return results

    def get_retention_stats(self) -> Dict[str, int]:
        """
        Get statistics about data retention compliance.

        Returns:
            Dictionary with data counts by category
        """
        try:
            stats = {}

            # Count sessions by age
            from ..models.session import Session
            now = datetime.utcnow()
            stats["active_sessions"] = self.db.query(Session).filter(Session.is_active == True).count()
            stats["expired_sessions_30d"] = self.db.query(Session).filter(
                Session.expires_at < now - timedelta(days=30)
            ).count()

            # Count audit logs by age
            from ..models.audit import AuditLog
            stats["audit_logs_total"] = self.db.query(AuditLog).count()
            stats["audit_logs_1year"] = self.db.query(AuditLog).filter(
                AuditLog.created_at < now - timedelta(days=365)
            ).count()
            stats["audit_logs_7years"] = self.db.query(AuditLog).filter(
                AuditLog.created_at < now - timedelta(days=7*365)
            ).count()

            # Count usage records
            from ..models.usage import Usage
            stats["usage_records"] = self.db.query(Usage).count()

            # Count user feedback
            from ..models.user_feedback import UserFeedback
            stats["user_feedback_total"] = self.db.query(UserFeedback).count()
            stats["user_feedback_3years"] = self.db.query(UserFeedback).filter(
                UserFeedback.created_at < now - timedelta(days=3*365)
            ).count()

            return stats

        except Exception as e:
            logger.error(f"Error getting retention stats: {e}")
            return {}
