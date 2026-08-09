"""add_company_macro_tables

Revision ID: 422l1d347c28
Revises: 421k1d347c27
Create Date: 2026-06-18 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "422l1d347c28"
down_revision: str | Sequence[str] | None = "421k1d347c27"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # company_macro_inputs
    op.create_table(
        "company_macro_inputs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("period_label", sa.String(length=40), nullable=False),
        sa.Column("period_end_date", sa.Date(), nullable=True),
        sa.Column("operating_income", sa.Float(), nullable=True),
        sa.Column("market_cap", sa.Float(), nullable=True),
        sa.Column("total_debt", sa.Float(), nullable=True),
        sa.Column("cash", sa.Float(), nullable=True),
        sa.Column("enterprise_value", sa.Float(), nullable=True),
        sa.Column("source_document_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_company_macro_inputs_company_id"), "company_macro_inputs", ["company_id"], unique=False)
    op.create_index(op.f("ix_company_macro_inputs_period_label"), "company_macro_inputs", ["period_label"], unique=False)

    # company_macro_sensitivity_results
    op.create_table(
        "company_macro_sensitivity_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("valuation_id", sa.Integer(), nullable=True),
        sa.Column("method", sa.String(length=40), nullable=False),
        sa.Column("dependent_variable", sa.String(length=40), nullable=False),
        sa.Column("observation_count", sa.Integer(), nullable=True),
        sa.Column("duration", sa.Float(), nullable=True),
        sa.Column("cyclicality", sa.Float(), nullable=True),
        sa.Column("inflation_sensitivity", sa.Float(), nullable=True),
        sa.Column("currency_sensitivity", sa.Float(), nullable=True),
        sa.Column("rate_slope", sa.Float(), nullable=True),
        sa.Column("gdp_slope", sa.Float(), nullable=True),
        sa.Column("inflation_slope", sa.Float(), nullable=True),
        sa.Column("currency_slope", sa.Float(), nullable=True),
        sa.Column("regression_r_squared", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("confidence_label", sa.String(length=40), nullable=True),
        sa.Column("warnings", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ),
        sa.ForeignKeyConstraint(["valuation_id"], ["valuation_models.id"], ),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_company_macro_sensitivity_results_company_id"), "company_macro_sensitivity_results", ["company_id"], unique=False)
    op.create_index(op.f("ix_company_macro_sensitivity_results_valuation_id"), "company_macro_sensitivity_results", ["valuation_id"], unique=False)

    # company_macro_segment_exposures
    op.create_table(
        "company_macro_segment_exposures",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("valuation_id", sa.Integer(), nullable=True),
        sa.Column("segment_name", sa.String(length=255), nullable=False),
        sa.Column("sic_code", sa.String(length=20), nullable=True),
        sa.Column("benchmark_industry_name", sa.String(length=255), nullable=True),
        sa.Column("segment_value", sa.Float(), nullable=True),
        sa.Column("segment_revenue", sa.Float(), nullable=True),
        sa.Column("segment_weight", sa.Float(), nullable=True),
        sa.Column("duration", sa.Float(), nullable=True),
        sa.Column("cyclicality", sa.Float(), nullable=True),
        sa.Column("inflation_sensitivity", sa.Float(), nullable=True),
        sa.Column("currency_sensitivity", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ),
        sa.ForeignKeyConstraint(["valuation_id"], ["valuation_models.id"], ),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index(op.f("ix_company_macro_segment_exposures_company_id"), "company_macro_segment_exposures", ["company_id"], unique=False)
    op.create_index(op.f("ix_company_macro_segment_exposures_valuation_id"), "company_macro_segment_exposures", ["valuation_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_company_macro_segment_exposures_valuation_id"), table_name="company_macro_segment_exposures")
    op.drop_index(op.f("ix_company_macro_segment_exposures_company_id"), table_name="company_macro_segment_exposures")
    op.drop_table("company_macro_segment_exposures")

    op.drop_index(op.f("ix_company_macro_sensitivity_results_valuation_id"), table_name="company_macro_sensitivity_results")
    op.drop_index(op.f("ix_company_macro_sensitivity_results_company_id"), table_name="company_macro_sensitivity_results")
    op.drop_table("company_macro_sensitivity_results")

    op.drop_index(op.f("ix_company_macro_inputs_period_label"), table_name="company_macro_inputs")
    op.drop_index(op.f("ix_company_macro_inputs_company_id"), table_name="company_macro_inputs")
    op.drop_table("company_macro_inputs")
