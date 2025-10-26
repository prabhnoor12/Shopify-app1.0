"""
Service for user-related business logic (profile, usage, stats, search, etc.).
"""

from sqlalchemy.orm import Session
from ..models.shop import ShopifyUser
from typing import Optional, List
import csv
import io
import json
import xml.etree.ElementTree as ET
from datetime import datetime


class UserService:
    """
    Provides business logic for user management, stats, and search.
    """

    # --- Robust User Management Features ---

    def activate_user(self, user_id: int) -> Optional[ShopifyUser]:
        """Activate a user account."""
        user = self.get_user_by_id(user_id)
        if user:
            user.is_active = True
            self.db.commit()
            self.db.refresh(user)
        return user

    def deactivate_user(self, user_id: int) -> Optional[ShopifyUser]:
        """Deactivate a user account."""
        user = self.get_user_by_id(user_id)
        if user:
            user.is_active = False
            self.db.commit()
            self.db.refresh(user)
        return user

    def update_password(self, user_id: int, new_password: str) -> Optional[ShopifyUser]:
        """Update a user's password (expects hashed password)."""
        user = self.get_user_by_id(user_id)
        if user:
            user.hashed_password = new_password
            self.db.commit()
            self.db.refresh(user)
        return user

    def update_last_login(self, user_id: int) -> Optional[ShopifyUser]:
        """Update the last login timestamp for a user."""
        from sqlalchemy.sql import func
        user = self.get_user_by_id(user_id)
        if user:
            user.last_login = func.now()
            self.db.commit()
            self.db.refresh(user)
        return user

    def update_profile(self, user_id: int, profile_data: dict) -> Optional[ShopifyUser]:
        """Update user profile fields (email, etc)."""
        user = self.get_user_by_id(user_id)
        if user:
            for key, value in profile_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            self.db.commit()
            self.db.refresh(user)
        return user

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: int) -> Optional[ShopifyUser]:
        """Get a user by their ID. Returns None if not found."""
        try:
            from my_app.crud.user_crud import get_user
            return get_user(self.db, user_id)
        except Exception as e:
            # Log error if logger available
            return None

    def get_user_by_email(self, email: str) -> Optional[ShopifyUser]:
        """Get a user by their email address."""
        try:
            from my_app.crud.user_crud import get_user_by_email
            return get_user_by_email(self.db, email)
        except Exception:
            return None

    def list_users(self, skip: int = 0, limit: int = 100) -> List[ShopifyUser]:
        """List users with pagination."""
        try:
            from my_app.crud.user_crud import get_users
            return get_users(self.db, skip=skip, limit=limit)
        except Exception:
            return []

    def create_user(self, user_data: dict) -> Optional[ShopifyUser]:
        """Create a new user."""
        try:
            from my_app.crud.user_crud import create_user
            return create_user(self.db, user_data)
        except Exception:
            return None

    def update_user(self, user_id: int, user_update: dict) -> Optional[ShopifyUser]:
        """Update user fields using the CRUD layer."""
        try:
            from my_app.crud.user_crud import update_user
            return update_user(self.db, user_id, user_update)
        except Exception:
            return None

    def delete_user(self, user_id: int) -> Optional[ShopifyUser]:
        """Delete a user by ID."""
        try:
            from my_app.crud.user_crud import delete_user
            return delete_user(self.db, user_id)
        except Exception:
            return None

    def get_user_stats(self, shop_domain: str) -> Optional[dict]:
        """Get usage stats for a user (e.g., generations used)."""
        user = self.get_user_by_email(shop_domain)  # or by shop_domain if available
        if user:
            return {
                "shop_domain": getattr(user, "shop_domain", None),
                "generations_used": getattr(user, "generations_used", None),
                "created_at": user.created_at,
            }
        return None

    def search_users(self, query: str) -> List[ShopifyUser]:
        """Search users by partial shop domain match (case-insensitive)."""
        try:
            return (
                self.db.query(ShopifyUser)
                .filter(ShopifyUser.shop_domain.ilike(f"%{query}%"))
                .all()
            )
        except Exception:
            return []

    def export_user_data(self, user_id: int, format_type: str = "json") -> Optional[dict]:
        """Export all personal data for a user for GDPR compliance."""
        user = self.get_user_by_id(user_id)
        if not user:
            return None

        # Get user basic data
        user_data = {
            "id": user.id,
            "email": user.email,
            "shop_domain": user.shop_domain,
            "is_active": user.is_active,
            "plan": user.plan,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
        }

        # Get audit logs
        from ..models.audit import AuditLog
        audit_logs = (
            self.db.query(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(1000)  # Limit to prevent huge exports
            .all()
        )

        audit_data = []
        for log in audit_logs:
            audit_data.append({
                "id": log.id,
                "event_type": log.event_type,
                "action": log.action,
                "details": log.details,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            })

        # Get sessions
        from ..models.session import Session
        sessions = (
            self.db.query(Session)
            .filter(Session.user_id == user_id)
            .order_by(Session.created_at.desc())
            .limit(100)  # Limit sessions
            .all()
        )

        session_data = []
        for session in sessions:
            session_data.append({
                "id": session.id,
                "session_token": session.session_token[:10] + "..." if session.session_token else None,  # Mask token
                "ip_address": session.ip_address,
                "user_agent": session.user_agent,
                "is_active": session.is_active,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "expires_at": session.expires_at.isoformat() if session.expires_at else None,
            })

        # Get usage data
        from ..models.usage import Usage
        usage = (
            self.db.query(Usage)
            .filter(Usage.user_id == user_id)
            .first()
        )

        usage_data = {}
        if usage:
            usage_data = {
                "total_requests": usage.total_requests,
                "monthly_requests": usage.monthly_requests,
                "last_reset": usage.last_reset.isoformat() if usage.last_reset else None,
            }

        # Aggregate all data
        data = {
            "user_data": user_data,
            "audit_logs": audit_data,
            "sessions": session_data,
            "usage_data": usage_data,
            "export_date": datetime.now().isoformat(),
        }

        # Return data in requested format
        if format_type == "json":
            return data
        elif format_type == "csv":
            return self._export_as_csv(data)
        elif format_type == "xml":
            return self._export_as_xml(data)
        else:
            return data  # Default to JSON

    def _export_as_csv(self, data: dict) -> str:
        """Export user data as CSV format."""
        output = io.StringIO()

        # User data section
        output.write("=== USER DATA ===\n")
        writer = csv.writer(output)
        writer.writerow(["Field", "Value"])
        for key, value in data["user_data"].items():
            writer.writerow([key, str(value)])
        output.write("\n")

        # Audit logs section
        output.write("=== AUDIT LOGS ===\n")
        if data["audit_logs"]:
            writer = csv.writer(output)
            writer.writerow(["ID", "Event Type", "Action", "Details", "IP Address", "User Agent", "Created At"])
            for log in data["audit_logs"]:
                writer.writerow([
                    log["id"], log["event_type"], log["action"], log["details"],
                    log["ip_address"], log["user_agent"], log["created_at"]
                ])
        output.write("\n")

        # Sessions section
        output.write("=== SESSIONS ===\n")
        if data["sessions"]:
            writer = csv.writer(output)
            writer.writerow(["ID", "Session Token", "IP Address", "User Agent", "Is Active", "Created At", "Expires At"])
            for session in data["sessions"]:
                writer.writerow([
                    session["id"], session["session_token"], session["ip_address"],
                    session["user_agent"], session["is_active"], session["created_at"], session["expires_at"]
                ])
        output.write("\n")

        # Usage data section
        output.write("=== USAGE DATA ===\n")
        writer = csv.writer(output)
        writer.writerow(["Field", "Value"])
        for key, value in data["usage_data"].items():
            writer.writerow([key, str(value)])

        return output.getvalue()

    def _export_as_xml(self, data: dict) -> str:
        """Export user data as XML format."""
        root = ET.Element("UserDataExport")
        root.set("export_date", data["export_date"])

        # User data
        user_elem = ET.SubElement(root, "UserData")
        for key, value in data["user_data"].items():
            child = ET.SubElement(user_elem, key)
            child.text = str(value) if value is not None else ""

        # Audit logs
        audit_logs_elem = ET.SubElement(root, "AuditLogs")
        for log in data["audit_logs"]:
            log_elem = ET.SubElement(audit_logs_elem, "AuditLog")
            for key, value in log.items():
                child = ET.SubElement(log_elem, key)
                child.text = str(value) if value is not None else ""

        # Sessions
        sessions_elem = ET.SubElement(root, "Sessions")
        for session in data["sessions"]:
            session_elem = ET.SubElement(sessions_elem, "Session")
            for key, value in session.items():
                child = ET.SubElement(session_elem, key)
                child.text = str(value) if value is not None else ""

        # Usage data
        usage_elem = ET.SubElement(root, "UsageData")
        for key, value in data["usage_data"].items():
            child = ET.SubElement(usage_elem, key)
            child.text = str(value) if value is not None else ""

        # Convert to string
        rough_string = ET.tostring(root, encoding='unicode')
        return rough_string

    def delete_user_data(self, user_id: int) -> bool:
        """Delete all personal data for a user for GDPR compliance."""
        user = self.get_user_by_id(user_id)
        if not user:
            return False

        try:
            # Delete audit logs
            from ..models.audit import AuditLog
            self.db.query(AuditLog).filter(AuditLog.user_id == user_id).delete()

            # Delete sessions
            from ..models.session import Session
            self.db.query(Session).filter(Session.user_id == user_id).delete()

            # Delete usage data
            from ..models.usage import Usage
            self.db.query(Usage).filter(Usage.user_id == user_id).delete()

            # Delete user feedback
            from ..models.user_feedback import UserFeedback
            self.db.query(UserFeedback).filter(UserFeedback.user_id == user_id).delete()

            # Anonymize user data instead of deleting (safer approach)
            # This preserves referential integrity while removing personal data
            user.email = f"deleted_{user_id}@anonymous.local"
            user.hashed_password = "DELETED"
            user.is_active = False
            # Keep shop_domain for system functionality but anonymize other data

            self.db.commit()
            return True

        except Exception as e:
            self.db.rollback()
            # Log error here
            return False

    def rectify_user_data(self, user_id: int, field: str, new_value: str, reason: str = None) -> bool:
        """Update/rectify personal data for a user for GDPR compliance."""
        user = self.get_user_by_id(user_id)
        if not user:
            return False

        # Define allowed fields for rectification
        allowed_fields = {
            "email": lambda u, v: setattr(u, "email", v),
            "shop_domain": lambda u, v: setattr(u, "shop_domain", v),
            "plan": lambda u, v: setattr(u, "plan", v),
        }

        if field not in allowed_fields:
            return False

        try:
            # Store old value for audit logging
            old_value = getattr(user, field)

            # Update the field
            allowed_fields[field](user, new_value)

            # Log the rectification
            from ..models.audit import AuditLog
            audit_log = AuditLog(
                user_id=user_id,
                shop_id=getattr(user, 'shop_id', None),
                event_type="data_rectification",
                action=f"Updated {field}",
                details=json.dumps({
                    "field": field,
                    "old_value": str(old_value),
                    "new_value": str(new_value),
                    "reason": reason
                }),
                ip_address="system",  # In production, get from request
                user_agent="GDPR Rectification API"
            )
            self.db.add(audit_log)

            self.db.commit()
            return True

        except Exception as e:
            self.db.rollback()
            # Log error here
            return False
