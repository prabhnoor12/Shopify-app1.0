import json
import pandas as pd
from my_app.models.audit import AuditLog
from sqlalchemy.sql import func
from sqlalchemy.orm import Session
from datetime import datetime, timedelta


def export_audit_logs_to_json(logs):
    """
    Export a list of audit log SQLAlchemy objects to JSON string.
    """
    try:
        logs_list = []
        for log in logs:
            logs_list.append(
                {
                    "id": log.id,
                    "user_id": log.user_id,
                    "shop_id": log.shop_id,
                    "event_type": log.event_type,
                    "action": log.action,
                    "details": log.details,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "created_at": log.created_at.isoformat()
                    if log.created_at
                    else None,
                }
            )
        return json.dumps(logs_list, indent=2)
    except Exception as e:
        print(f"Error exporting audit logs to JSON: {e}")
        return "[]"


def export_audit_logs_to_excel(logs, file_path):
    """
    Export a list of audit log SQLAlchemy objects to an Excel file.
    """
    try:
        logs_list = []
        for log in logs:
            logs_list.append(
                {
                    "id": log.id,
                    "user_id": log.user_id,
                    "shop_id": log.shop_id,
                    "event_type": log.event_type,
                    "action": log.action,
                    "details": str(log.details),
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                    "created_at": log.created_at.isoformat()
                    if log.created_at
                    else None,
                }
            )
        df = pd.DataFrame(logs_list)
        df.to_excel(file_path, index=False)
        print(f"Audit logs exported to Excel: {file_path}")
        return True
    except Exception as e:
        print(f"Error exporting audit logs to Excel: {e}")
        return False


def get_event_counts_by_user(db: Session):
    """
    Returns a summary of event counts grouped by user_id.
    """
    try:
        results = (
            db.query(AuditLog.user_id, func.count(AuditLog.id).label("event_count"))
            .group_by(AuditLog.user_id)
            .all()
        )
        return results
    except Exception as e:
        print(f"Error aggregating event counts by user: {e}")
        return []


def get_event_counts_by_shop(db: Session):
    """
    Returns a summary of event counts grouped by shop_id.
    """
    try:
        results = (
            db.query(AuditLog.shop_id, func.count(AuditLog.id).label("event_count"))
            .group_by(AuditLog.shop_id)
            .all()
        )
        return results
    except Exception as e:
        print(f"Error aggregating event counts by shop: {e}")
        return []


def get_event_counts_by_type(db: Session):
    """
    Returns a summary of event counts grouped by event_type.
    """
    try:
        results = (
            db.query(AuditLog.event_type, func.count(AuditLog.id).label("event_count"))
            .group_by(AuditLog.event_type)
            .all()
        )
        return results
    except Exception as e:
        print(f"Error aggregating event counts by type: {e}")
        return []


def create_audit(db: Session, audit: dict):
    # Basic input validation
    required_fields = ["user_id", "shop_id", "event_type", "action", "details"]
    for field in required_fields:
        if field not in audit:
            print(f"Missing required field: {field}")
            return None
    try:
        db_audit = AuditLog(**audit)
        db.add(db_audit)
        db.commit()
        db.refresh(db_audit)
        print(f"Audit created: {db_audit.id}")
        return db_audit
    except Exception as e:
        print(f"Error creating audit: {e}")
        db.rollback()
        return None


def search_audit_logs(db: Session, query_str: str, skip: int = 0, limit: int = 50):
    """
    Search audit logs across multiple fields: action, details, event_type, user_agent.
    """
    try:
        search_filter = (
            (AuditLog.action.ilike(f"%{query_str}%"))
            | (AuditLog.details.astext.ilike(f"%{query_str}%"))
            | (AuditLog.event_type.ilike(f"%{query_str}%"))
            | (AuditLog.user_agent.ilike(f"%{query_str}%"))
        )
        results = (
            db.query(AuditLog)
            .filter(search_filter)
            .order_by(AuditLog.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return results
    except Exception as e:
        print(f"Error searching audit logs: {e}")
        return []


def delete_old_audit_logs(db: Session, days: int = 90):
    """
    Delete audit logs older than the specified number of days (default: 90).
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        old_logs = db.query(AuditLog).filter(AuditLog.created_at < cutoff_date).all()
        count = 0
        for log in old_logs:
            db.delete(log)
            count += 1
        db.commit()
        print(f"Deleted {count} audit logs older than {days} days.")
        return count
    except Exception as e:
        print(f"Error deleting old audit logs: {e}")
        db.rollback()
        return 0


def get_audit(db: Session, audit_id: int):
    try:
        audit = db.query(AuditLog).filter(AuditLog.id == audit_id).first()
        return audit
    except Exception as e:
        print(f"Error getting audit: {e}")
        return None


def get_audits(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    user_id: int = None,
    shop_id: int = None,
    event_type: str = None,
    start: datetime = None,
    end: datetime = None,
):
    try:
        query = db.query(AuditLog)
        if user_id is not None:
            query = query.filter(AuditLog.user_id == user_id)
        if shop_id is not None:
            query = query.filter(AuditLog.shop_id == shop_id)
        if event_type is not None:
            query = query.filter(AuditLog.event_type == event_type)
        if start is not None:
            query = query.filter(AuditLog.created_at >= start)
        if end is not None:
            query = query.filter(AuditLog.created_at <= end)
        audits = (
            query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
        )
        return audits
    except Exception as e:
        print(f"Error getting audits: {e}")
        return []


def create_audit(db: Session, audit: dict):
    # Basic input validation
    required_fields = ["user_id", "shop_id", "event_type", "action", "details"]
    for field in required_fields:
        if field not in audit:
            print(f"Missing required field: {field}")
            return None
    try:
        db_audit = AuditLog(**audit)
        db.add(db_audit)
        db.commit()
        db.refresh(db_audit)
        print(f"Audit created: {db_audit.id}")
        return db_audit
    except Exception as e:
        print(f"Error creating audit: {e}")
        db.rollback()
        return None


def update_audit(db: Session, audit_id: int, audit_update: dict):
    try:
        db_audit = db.query(AuditLog).filter(AuditLog.id == audit_id).first()
        if db_audit:
            for key, value in audit_update.items():
                setattr(db_audit, key, value)
            db.commit()
            db.refresh(db_audit)
            print(f"Audit updated: {db_audit.id}")
        return db_audit
    except Exception as e:
        print(f"Error updating audit: {e}")
        db.rollback()
        return None


def soft_delete_audit_log(db: Session, audit_id: int):
    """
    Soft delete an audit log by setting deleted_at timestamp.
    """
    try:
        db_audit = db.query(AuditLog).filter(AuditLog.id == audit_id).first()
        if db_audit and db_audit.deleted_at is None:
            from datetime import datetime

            db_audit.deleted_at = datetime.utcnow()
            db.commit()
            db.refresh(db_audit)
            print(f"Audit soft deleted: {db_audit.id}")
        return db_audit
    except Exception as e:
        print(f"Error soft deleting audit: {e}")
        db.rollback()
        return None
