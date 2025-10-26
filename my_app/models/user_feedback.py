import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from ..database import Base


class FeedbackStatus(str, Enum):
    ACCEPTED = "accepted"
    EDITED = "edited"
    REJECTED = "rejected"


class UserFeedback(Base):
    """
    SQLAlchemy model for user feedback on generated content.
    """

    __tablename__ = "user_feedback"

    id: int = sa.Column(sa.Integer, primary_key=True, index=True)
    user_id: int = sa.Column(
        sa.Integer,
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_text: str = sa.Column(sa.Text, nullable=False)
    edited_text: str = sa.Column(sa.Text, nullable=True)
    status: str = sa.Column(
        sa.String, nullable=False, comment="Enum: 'accepted', 'edited', 'rejected'"
    )
    created_at = sa.Column(
        sa.DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user = relationship("User")
