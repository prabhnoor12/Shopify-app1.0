import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class MemoryVaultEntry(Base):
    __tablename__ = "memory_vault_entries"

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    user_id = sa.Column(
        sa.Integer,
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content = sa.Column(
        sa.Text,
        nullable=False,
        comment="A specific fact or piece of information for the AI to remember.",
    )
    is_active = sa.Column(sa.Boolean, default=True, nullable=False)
    created_at = sa.Column(
        sa.DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = sa.Column(sa.DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="memory_vault_entries")
