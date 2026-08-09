"""add market regime input provenance

Revision ID: bb3bb3bb3bb3
Revises: aa2aa2aa2aa2
Create Date: 2026-08-09 20:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "bb3bb3bb3bb3"
down_revision: str | None = "aa2aa2aa2aa2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "market_regime_inputs",
        sa.Column("source_name", sa.String(length=200), server_default="Legacy input", nullable=False),
    )
    op.add_column(
        "market_regime_inputs",
        sa.Column("input_type", sa.String(length=30), server_default="manual", nullable=False),
    )
    op.add_column(
        "market_regime_inputs",
        sa.Column(
            "methodology",
            sa.String(length=1000),
            server_default="Legacy input without recorded methodology.",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("market_regime_inputs", "methodology")
    op.drop_column("market_regime_inputs", "input_type")
    op.drop_column("market_regime_inputs", "source_name")
