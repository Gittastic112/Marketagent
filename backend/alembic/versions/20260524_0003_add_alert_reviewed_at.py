"""add alert reviewed_at

Revision ID: 20260524_0003
Revises: 20260524_0002
Create Date: 2026-05-24
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260524_0003"
down_revision: str | Sequence[str] | None = "20260524_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("alerts", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("alerts", "reviewed_at")
