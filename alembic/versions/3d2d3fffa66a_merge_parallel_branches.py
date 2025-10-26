"""Merge parallel branches

Revision ID: 3d2d3fffa66a
Revises: 23abce99558c, e2a5c2a7b3d9
Create Date: 2025-09-06 12:05:57.647839

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "3d2d3fffa66a"
down_revision: Union[str, Sequence[str], None] = ("23abce99558c", "e2a5c2a7b3d9")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
