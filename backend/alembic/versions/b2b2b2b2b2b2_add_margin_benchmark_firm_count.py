"""add margin benchmark firm count

Revision ID: b2b2b2b2b2b2
Revises: a1a1a1a1a1a1
Create Date: 2026-06-21 08:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "b2b2b2b2b2b2"
down_revision: str | Sequence[str] | None = "a1a1a1a1a1a1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "damodaran_industry_margin_benchmarks",
        sa.Column("number_of_firms", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("damodaran_industry_margin_benchmarks", "number_of_firms")
