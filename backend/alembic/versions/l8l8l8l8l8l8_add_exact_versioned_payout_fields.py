"""Add exact fields for versioned working-capital and payout sources.

Revision ID: l8l8l8l8l8l8
Revises: k7k7k7k7k7k7
Create Date: 2026-08-08
"""

import sqlalchemy as sa
from alembic import op


revision = "l8l8l8l8l8l8"
down_revision = "k7k7k7k7k7k7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "damodaran_industry_working_capital_benchmarks",
        sa.Column("number_of_firms", sa.Integer(), nullable=True),
    )
    op.add_column(
        "damodaran_industry_dividend_benchmarks",
        sa.Column("number_of_firms", sa.Integer(), nullable=True),
    )
    op.add_column(
        "damodaran_industry_fcfe_benchmarks",
        sa.Column("number_of_firms", sa.Integer(), nullable=True),
    )
    op.add_column(
        "damodaran_industry_fcfe_benchmarks",
        sa.Column("fcfe_before_debt", sa.Float(), nullable=True),
    )
    op.add_column(
        "damodaran_industry_fcfe_benchmarks",
        sa.Column("fcfe_after_debt", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("damodaran_industry_fcfe_benchmarks", "fcfe_after_debt")
    op.drop_column("damodaran_industry_fcfe_benchmarks", "fcfe_before_debt")
    op.drop_column("damodaran_industry_fcfe_benchmarks", "number_of_firms")
    op.drop_column("damodaran_industry_dividend_benchmarks", "number_of_firms")
    op.drop_column("damodaran_industry_working_capital_benchmarks", "number_of_firms")
