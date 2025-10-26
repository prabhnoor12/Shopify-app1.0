"""
This module defines the database model for content approval requests,
which are used by agencies to get client sign-off on generated content.
"""

import enum
import secrets
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


def generate_token():
    """Generates a secure, URL-safe token."""
    return secrets.token_urlsafe(32)


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, default=generate_token)

    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, nullable=False)  # Assuming this links to a product

    content_to_approve = Column(Text, nullable=False)
    status = Column(
        SQLEnum(ApprovalStatus), default=ApprovalStatus.PENDING, nullable=False
    )
    client_comment = Column(Text)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at = Column(
        DateTime(timezone=True)
    )  # Optional: for time-sensitive approvals

    agency = relationship("Agency")
    requester = relationship("User")
    # If you have a Product model, you can add a relationship here
    # product = relationship("Product")
