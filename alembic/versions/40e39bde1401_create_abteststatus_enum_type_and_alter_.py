"""create abteststatus enum type and alter ab_tests table

Revision ID: <new_revision_id>
Revises: a5ad76290d43
Create Date: 2025-09-04 11:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "40e39bde1401"
down_revision: Union[str, Sequence[str], None] = "e2a5c2a7b3d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define the ENUM type
abteststatus_enum = sa.Enum(
    "DRAFT", "RUNNING", "PAUSED", "FINISHED", "CONCLUDED", name="abteststatus"
)


def upgrade() -> None:
    """Upgrade schema."""
    # Create the ENUM type in the database
    abteststatus_enum.create(op.get_bind(), checkfirst=True)

    # Alter the column to use the new ENUM type
    op.alter_column(
        "ab_tests",
        "status",
        existing_type=sa.VARCHAR(),
        type_=abteststatus_enum,
        existing_nullable=True,
        postgresql_using="status::text::abteststatus",
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Alter the column back to VARCHAR
    op.alter_column(
        "ab_tests",
        "status",
        existing_type=abteststatus_enum,
        type_=sa.VARCHAR(),
        existing_nullable=True,
    )

    # Drop the ENUM type from the database
    abteststatus_enum.drop(op.get_bind(), checkfirst=True)
