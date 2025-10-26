"""Change AuditLog.details from Text to JSON

Revision ID: e2a5c2a7b3d9
Revises: a5ad76290d43
Create Date: 2025-09-04 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e2a5c2a7b3d9"
down_revision: Union[str, Sequence[str], None] = "0131719c6439"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "audit_logs",
        "details",
        existing_type=sa.Text(),
        type_=postgresql.JSONB(astext_type=sa.Text()),
        postgresql_using="details::jsonb",
    )


def downgrade() -> None:
    op.alter_column(
        "audit_logs",
        "details",
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        type_=sa.Text(),
        postgresql_using="details::text",
    )
