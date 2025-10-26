"""add brand voice table

Revision ID: 87cc755db627
Revises: 3a30a9fd93dd
Create Date: 2025-09-03 18:16:27.024177

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "87cc755db627"
down_revision: Union[str, Sequence[str], None] = "3a30a9fd93dd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
