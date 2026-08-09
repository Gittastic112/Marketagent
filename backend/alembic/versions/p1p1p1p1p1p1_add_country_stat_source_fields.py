"""Add complete country-statistics source fields.

Revision ID: p1p1p1p1p1p1
Revises: n0n0n0n0n0n0
Create Date: 2026-08-08
"""

import sqlalchemy as sa
from alembic import op


revision = "p1p1p1p1p1p1"
down_revision = "n0n0n0n0n0n0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "country_market_stats",
        sa.Column("median_cash_to_firm_value", sa.Float(), nullable=True),
    )
    op.add_column(
        "country_market_stats",
        sa.Column("total_dividends_usd_millions", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("country_market_stats", "total_dividends_usd_millions")
    op.drop_column("country_market_stats", "median_cash_to_firm_value")
