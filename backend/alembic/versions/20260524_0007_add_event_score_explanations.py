"""add event score explanations

Revision ID: 20260524_0007
Revises: 20260524_0006
Create Date: 2026-05-24
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260524_0007"
down_revision: str | Sequence[str] | None = "20260524_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("events", sa.Column("score_explanation_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("events", "score_explanation_json")
