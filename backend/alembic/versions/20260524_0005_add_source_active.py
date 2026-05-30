"""add source active flag

Revision ID: 20260524_0005
Revises: 20260524_0004
Create Date: 2026-05-24
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260524_0005"
down_revision: str | Sequence[str] | None = "20260524_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("sources", sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False))


def downgrade() -> None:
    op.drop_column("sources", "active")
