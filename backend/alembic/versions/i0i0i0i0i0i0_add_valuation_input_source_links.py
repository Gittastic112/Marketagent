"""add valuation input source links

Revision ID: i0i0i0i0i0i0
Revises: h9h9h9h9h9h9
Create Date: 2026-08-25 15:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "i0i0i0i0i0i0"
down_revision: str | None = "h9h9h9h9h9h9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "assumption_method_values",
        sa.Column("dataset_file_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_assumption_method_values_dataset_file_id",
        "assumption_method_values",
        "damodaran_dataset_files",
        ["dataset_file_id"],
        ["id"],
    )
    op.create_index(
        "ix_assumption_method_values_dataset_file_id",
        "assumption_method_values",
        ["dataset_file_id"],
        unique=False,
    )

    for column_name in (
        "dividends_usd_millions",
        "buybacks_usd_millions",
        "equity_issuance_usd_millions",
        "net_equity_change_usd_millions",
        "net_equity_change_to_book_equity",
        "debt_repaid_usd_millions",
        "debt_raised_usd_millions",
        "net_debt_change_usd_millions",
        "net_debt_change_to_total_debt",
        "lease_debt_change_usd_millions",
    ):
        op.add_column(
            "damodaran_industry_financing_flows",
            sa.Column(column_name, sa.Float(), nullable=True),
        )
    op.add_column(
        "damodaran_industry_financing_flows",
        sa.Column("number_of_firms", sa.Integer(), nullable=True),
    )
    for column_name in (
        "expected_revenue_growth_2y",
        "expected_revenue_growth_5y",
        "historical_net_income_growth",
    ):
        op.add_column(
            "damodaran_industry_fundamental_growth",
            sa.Column(column_name, sa.Float(), nullable=True),
        )


def downgrade() -> None:
    for column_name in (
        "historical_net_income_growth",
        "expected_revenue_growth_5y",
        "expected_revenue_growth_2y",
    ):
        op.drop_column("damodaran_industry_fundamental_growth", column_name)
    for column_name in (
        "lease_debt_change_usd_millions",
        "net_debt_change_to_total_debt",
        "net_debt_change_usd_millions",
        "debt_raised_usd_millions",
        "debt_repaid_usd_millions",
        "net_equity_change_to_book_equity",
        "net_equity_change_usd_millions",
        "equity_issuance_usd_millions",
        "buybacks_usd_millions",
        "dividends_usd_millions",
        "number_of_firms",
    ):
        op.drop_column("damodaran_industry_financing_flows", column_name)
    op.drop_index(
        "ix_assumption_method_values_dataset_file_id",
        table_name="assumption_method_values",
    )
    op.drop_constraint(
        "fk_assumption_method_values_dataset_file_id",
        "assumption_method_values",
        type_="foreignkey",
    )
    op.drop_column("assumption_method_values", "dataset_file_id")
