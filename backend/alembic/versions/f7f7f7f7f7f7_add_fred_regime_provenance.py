"""add FRED and market-regime provenance

Revision ID: f7f7f7f7f7f7
Revises: ee6ee6ee6ee6
Create Date: 2026-08-24 18:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f7f7f7f7f7f7"
down_revision: str | None = "ee6ee6ee6ee6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("macro_series", sa.Column("provider_name", sa.String(length=100), nullable=True))
    op.add_column("macro_series", sa.Column("source_url", sa.String(length=500), nullable=True))
    op.add_column(
        "market_regime_inputs",
        sa.Column("source_record_type", sa.String(length=80), nullable=True),
    )
    op.add_column(
        "market_regime_inputs",
        sa.Column("source_record_id", sa.Integer(), nullable=True),
    )
    op.create_unique_constraint(
        "uq_market_regime_provider_source_record",
        "market_regime_inputs",
        ["metric_name", "input_type", "source_record_type", "source_record_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_market_regime_provider_source_record",
        "market_regime_inputs",
        type_="unique",
    )
    op.drop_column("market_regime_inputs", "source_record_id")
    op.drop_column("market_regime_inputs", "source_record_type")
    op.drop_column("macro_series", "source_url")
    op.drop_column("macro_series", "provider_name")
