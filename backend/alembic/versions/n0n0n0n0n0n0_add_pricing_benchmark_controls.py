"""Add source-backed pricing benchmark interpretation controls.

Revision ID: n0n0n0n0n0n0
Revises: m9m9m9m9m9m9
Create Date: 2026-08-08
"""

import sqlalchemy as sa
from alembic import op


revision = "n0n0n0n0n0n0"
down_revision = "m9m9m9m9m9m9"
branch_labels = None
depends_on = None


TABLE = "damodaran_industry_pricing_benchmarks"
COLUMNS = (
    "pe_aggregate_all_firms",
    "pe_aggregate_money_making",
    "expected_growth_next_five_years",
    "roe",
    "roic",
    "net_margin",
    "pretax_operating_margin",
    "ev_to_ebitda_rd_positive_ebitda",
    "ev_to_ebitda_rd_all",
    "ev_to_after_tax_ebit_positive_ebitda",
    "ev_to_after_tax_ebit_all",
)


def upgrade() -> None:
    for column_name in COLUMNS:
        op.add_column(TABLE, sa.Column(column_name, sa.Float(), nullable=True))


def downgrade() -> None:
    for column_name in reversed(COLUMNS):
        op.drop_column(TABLE, column_name)
