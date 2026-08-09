"""add market regime score evidence

Revision ID: cc4cc4cc4cc4
Revises: bb3bb3bb3bb3
Create Date: 2026-08-09 21:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "cc4cc4cc4cc4"
down_revision: str | None = "bb3bb3bb3bb3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "market_regime_scores",
        sa.Column("calculation_status", sa.String(length=30), server_default="blocked", nullable=False),
    )
    op.add_column(
        "market_regime_scores",
        sa.Column("formula", sa.Text(), server_default="", nullable=False),
    )
    op.add_column(
        "market_regime_scores",
        sa.Column("blockers", sa.JSON(), server_default=sa.text("'[]'::json"), nullable=False),
    )
    op.add_column(
        "market_regime_scores",
        sa.Column("input_sources", sa.JSON(), server_default=sa.text("'[]'::json"), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("market_regime_scores", "input_sources")
    op.drop_column("market_regime_scores", "blockers")
    op.drop_column("market_regime_scores", "formula")
    op.drop_column("market_regime_scores", "calculation_status")
