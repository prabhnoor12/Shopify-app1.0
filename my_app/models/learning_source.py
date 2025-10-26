import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class LearningSource(Base):
    __tablename__ = "learning_sources"

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    user_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_type = sa.Column(
        sa.String,
        nullable=False,
        comment="Type of source, e.g., 'text', 'url', 'file'.",
    )
    content = sa.Column(
        sa.Text, nullable=True, comment="Raw text content, if applicable."
    )
    source_metadata = sa.Column(
        JSON,
        nullable=True,
        comment="Stores metadata like URL, filename, or processing status.",
    )
    is_active = sa.Column(sa.Boolean, default=True, nullable=False)
    created_at = sa.Column(
        sa.DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = sa.Column(sa.DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="learning_sources")
