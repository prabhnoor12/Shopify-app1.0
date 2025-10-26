"""Merge alembic heads

Revision ID: e5a5a4e3e2d1
Revises: 40e39bde1401, ac4606d15a50
Create Date: 2025-09-05 10:15:00.000000

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "e5a5a4e3e2d1"
down_revision: Union[str, Sequence[str], None] = ("40e39bde1401", "ac4606d15a50")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # This is a merge point, no database operations are needed.
    pass


def downgrade() -> None:
    """Downgrade schema."""
    # This is a merge point, no database operations are needed.
    pass
