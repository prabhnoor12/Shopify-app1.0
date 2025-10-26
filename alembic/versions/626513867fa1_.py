"""empty message

Revision ID: 626513867fa1
Revises: 1b4e3b8e6a3e, 88495b136a0c
Create Date: 2025-09-10 16:36:49.772696

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "626513867fa1"
down_revision: Union[str, Sequence[str], None] = "1b4e3b8e6a3e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
