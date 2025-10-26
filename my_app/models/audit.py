"""
AuditLog SQLAlchemy model for tracking user/shop actions, changes, and context.

Fields:
    - id: Primary key
    - user_id: User who performed the action
    - shop_id: Shop context for the action
    - event_type: Type of event (login, update, webhook, etc.)
    - action: Description of the action
    - details: JSON details of changes
    - ip_address: IP address of the actor
    - user_agent: User agent string
    - severity: Severity level (info, warning, critical)
    - tags: Comma-separated tags for categorization
    - source: Source of the event (api, web, system)
    - created_at: Timestamp of creation
    - deleted_at: Timestamp of soft deletion
All relevant fields are indexed for performance.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSON  # Import JSON type
from ..database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: int = Column(Integer, primary_key=True, index=True)
    user_id: int = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    shop_id: int = Column(
        Integer, ForeignKey("shopify_users.id"), nullable=True, index=True
    )
    event_type: str = Column(
        String, index=True, doc="Type of event (login, update, webhook, etc.)"
    )
    action: str = Column(String, doc="Description of the action performed.")
    details: dict = Column(
        JSON, doc="JSON details of changes or metadata, including before/after states."
    )
    target_entity: str = Column(
        String,
        nullable=True,
        index=True,
        doc="The entity being acted upon (e.g., 'product', 'role').",
    )
    target_id: str = Column(
        String, nullable=True, index=True, doc="The ID of the entity being acted upon."
    )
    ip_address: str = Column(String, nullable=True, doc="IP address of the actor.")
    user_agent: str = Column(String, nullable=True, doc="User agent string.")
    severity: str = Column(
        String,
        nullable=True,
        index=True,
        doc="Severity level (info, warning, critical).",
    )
    tags: str = Column(
        Text, nullable=True, doc="Comma-separated tags for flexible categorization."
    )
    source: str = Column(
        String, nullable=True, index=True, doc="Source of the event (api, web, system)."
    )
    created_at: DateTime = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="Timestamp of creation.",
    )
    deleted_at: DateTime = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        doc="Timestamp of soft deletion.",
    )
    timestamp: DateTime = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp of the event.",
    )
