"""add daily brief reviewed timestamp

Revision ID: dd5dd5dd5dd5
Revises: cc4cc4cc4cc4
Create Date: 2026-08-23 09:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "dd5dd5dd5dd5"
down_revision: str | None = "cc4cc4cc4cc4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "daily_briefs",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("daily_briefs", "reviewed_at")
