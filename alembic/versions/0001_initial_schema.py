"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-15
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from bot.database.models import Base
    bind = op.get_bind()
    Base.metadata.create_all(bind, checkfirst=True)


def downgrade() -> None:
    from bot.database.models import Base
    bind = op.get_bind()
    Base.metadata.drop_all(bind)
