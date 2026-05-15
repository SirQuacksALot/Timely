"""Add rate limiting to appointment types

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-15
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE appointment_types ADD COLUMN IF NOT EXISTS max_concurrent_requests INTEGER NOT NULL DEFAULT 1"
    )


def downgrade() -> None:
    op.drop_column("appointment_types", "max_concurrent_requests")
