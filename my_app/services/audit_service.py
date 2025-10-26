import csv
from io import StringIO
from datetime import datetime

"""
Service for audit log creation and reporting.
"""
from sqlalchemy.orm import Session
from ..models.audit import AuditLog
from my_app.utils.model_changes import get_model_changes


class AuditLogService:
    """
    Service layer for audit log operations.
    Provides advanced filtering, bulk operations, pagination, aggregation, and export features.
    All methods are type-annotated and documented for clarity.
    """

    def __init__(self, db: Session):
        """
        Initialize AuditService with a SQLAlchemy session.
        :param db: SQLAlchemy Session
        """
        self.db = db

    def create_audit(self, audit_data: dict) -> AuditLog:
        """
        Create a single audit log entry.
        :param audit_data: Dictionary of audit log fields
        :return: AuditLog instance
        """
        from my_app.crud.audit_crud import create_audit

        return create_audit(self.db, audit_data)

    def bulk_create_audits(self, audits_data: list[dict]) -> list[AuditLog]:
        """
        Bulk create audit logs from a list of dicts.
        :param audits_data: List of audit log dictionaries
        :return: List of AuditLog instances
        """
        """
        Bulk create audit logs from a list of dicts.
        """
        from my_app.crud.audit_crud import create_audit

        results = []
        for audit_data in audits_data:
            result = create_audit(self.db, audit_data)
            results.append(result)
        return results

    def create_audit_event(
        self,
        model_instance,
        event_type: str,
        user_id: int = None,
        shop_id: int = None,
        ip_address: str = None,
        user_agent: str = None,
    ) -> None:
        """
        Create an audit log entry for a model event.
        :param model_instance: The model instance being audited
        :param event_type: Type of event
        :param user_id: User ID
        :param shop_id: Shop ID
        :param ip_address: IP address
        :param user_agent: User agent string
        """
        changes = get_model_changes(model_instance)
        if not changes:
            return

        audit_data = {
            "user_id": user_id,
            "shop_id": shop_id,
            "event_type": event_type,
            "action": f"{event_type} on {model_instance.__class__.__name__}",
            "details": changes,
            "ip_address": ip_address,
            "user_agent": user_agent,
        }
        self.create_audit(audit_data)

    def get_audit(self, audit_id: int) -> AuditLog:
        """
        Retrieve a single audit log entry by ID.
        :param audit_id: AuditLog ID
        :return: AuditLog instance
        """
        from my_app.crud.audit_crud import get_audit

        return get_audit(self.db, audit_id)

    def list_audits(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: int = None,
        shop_id: int = None,
        event_type: str = None,
        start: datetime = None,
        end: datetime = None,
        severity: str = None,
        source: str = None,
        tags: str = None,
        include_deleted: bool = False,
    ) -> list[AuditLog]:
        """
        List audit logs with advanced filtering and pagination.
        :param skip: Number of records to skip
        :param limit: Max number of records to return
        :param user_id: Filter by user ID
        :param shop_id: Filter by shop ID
        :param event_type: Filter by event type
        :param start: Filter by start date
        :param end: Filter by end date
        :param severity: Filter by severity
        :param source: Filter by source
        :param tags: Filter by tags
        :param include_deleted: Include soft-deleted logs
        :return: List of AuditLog instances
        """
        from my_app.crud.audit_crud import get_audits

        audits = get_audits(
            self.db,
            skip=skip,
            limit=limit,
            user_id=user_id,
            shop_id=shop_id,
            event_type=event_type,
            start=start,
            end=end,
        )
        # Filter by new fields and deleted status
        filtered = []
        for audit in audits:
            if not include_deleted and getattr(audit, "deleted_at", None):
                continue
            if severity and getattr(audit, "severity", None) != severity:
                continue
            if source and getattr(audit, "source", None) != source:
                continue
            if tags and tags not in (getattr(audit, "tags", "") or ""):
                continue
            filtered.append(audit)
        return filtered

    def update_audit(self, audit_id: int, audit_update: dict) -> AuditLog:
        """
        Update an audit log entry.
        :param audit_id: AuditLog ID
        :param audit_update: Dictionary of fields to update
        :return: Updated AuditLog instance
        """
        from my_app.crud.audit_crud import update_audit

        return update_audit(self.db, audit_id, audit_update)

    def delete_audit(self, audit_id: int) -> bool:
        """
        Hard delete an audit log entry.
        :param audit_id: AuditLog ID
        :return: True if deleted, False otherwise
        """
        from my_app.crud.audit_crud import delete_audit

        return delete_audit(self.db, audit_id)

    def list_audit_logs(
        self,
        skip: int = 0,
        limit: int = 50,
        start: datetime = None,
        end: datetime = None,
        event_type: str = None,
    ):
        query = self.db.query(AuditLog)
        if start:
            query = query.filter(AuditLog.created_at >= start)
        if end:
            query = query.filter(AuditLog.created_at <= end)
        if event_type:
            query = query.filter(AuditLog.event_type == event_type)
        return (
            query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
        )

    def export_audit_logs_to_csv(self, logs) -> str:
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "id",
                "user_id",
                "shop_id",
                "event_type",
                "action",
                "details",
                "ip_address",
                "user_agent",
                "created_at",
            ]
        )
        for log in logs:
            writer.writerow(
                [
                    log.id,
                    log.user_id,
                    log.shop_id,
                    log.event_type,
                    log.action,
                    log.details,
                    log.ip_address,
                    log.user_agent,
                    log.created_at,
                ]
            )
        return output.getvalue()

    def soft_delete_audit_log(self, audit_id: int) -> bool:
        """
        Soft delete an audit log entry by setting deleted_at.
        :param audit_id: AuditLog ID
        :return: True if soft deleted, False otherwise
        """
        from my_app.crud.audit_crud import soft_delete_audit_log

        result = soft_delete_audit_log(self.db, audit_id)
        return bool(result)

    def search_audit_logs(
        self, query: str, skip: int = 0, limit: int = 50
    ) -> list[AuditLog]:
        """
        Search audit logs across multiple fields.
        :param query: Search string
        :param skip: Number of records to skip
        :param limit: Max number of records to return
        :return: List of AuditLog instances
        """
        from my_app.crud.audit_crud import search_audit_logs

        return search_audit_logs(self.db, query, skip=skip, limit=limit)

    def get_user_audit_logs(
        self, user_id: int, skip: int = 0, limit: int = 50
    ) -> list[AuditLog]:
        """
        Get audit logs for a specific user.
        :param user_id: User ID
        :param skip: Number of records to skip
        :param limit: Max number of records to return
        :return: List of AuditLog instances
        """
        return self.list_audits(user_id=user_id, skip=skip, limit=limit)

    def get_shop_audit_logs(
        self, shop_id: int, skip: int = 0, limit: int = 50
    ) -> list[AuditLog]:
        """
        Get audit logs for a specific shop.
        :param shop_id: Shop ID
        :param skip: Number of records to skip
        :param limit: Max number of records to return
        :return: List of AuditLog instances
        """
        return self.list_audits(shop_id=shop_id, skip=skip, limit=limit)

    def get_event_counts_by_user(self) -> list:
        """
        Get summary of event counts grouped by user.
        :return: List of (user_id, event_count) tuples
        """
        from my_app.crud.audit_crud import get_event_counts_by_user

        return get_event_counts_by_user(self.db)

    def get_event_counts_by_shop(self) -> list:
        """
        Get summary of event counts grouped by shop.
        :return: List of (shop_id, event_count) tuples
        """
        from my_app.crud.audit_crud import get_event_counts_by_shop

        return get_event_counts_by_shop(self.db)

    def get_event_counts_by_type(self) -> list:
        """
        Get summary of event counts grouped by event type.
        :return: List of (event_type, event_count) tuples
        """
        from my_app.crud.audit_crud import get_event_counts_by_type

        return get_event_counts_by_type(self.db)

    def export_audit_logs_to_json(self, logs) -> str:
        """
        Export audit logs to JSON format.
        :param logs: List of AuditLog instances
        :return: JSON string
        """
        from my_app.crud.audit_crud import export_audit_logs_to_json

        return export_audit_logs_to_json(logs)

    def export_audit_logs_to_excel(self, logs, file_path: str) -> bool:
        """
        Export audit logs to Excel format.
        :param logs: List of AuditLog instances
        :param file_path: Path to save Excel file
        :return: True if successful, False otherwise
        """
        from my_app.crud.audit_crud import export_audit_logs_to_excel

        return export_audit_logs_to_excel(logs, file_path)
