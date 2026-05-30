"""add company aliases

Revision ID: 20260524_0006
Revises: 20260524_0005
Create Date: 2026-05-24
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260524_0006"
down_revision: str | Sequence[str] | None = "20260524_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("aliases_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("companies", "aliases_json")
