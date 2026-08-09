"""add portfolio performance foundation

Revision ID: aa2aa2aa2aa2
Revises: z1z1z1z1z1z1
Create Date: 2026-08-09 18:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "aa2aa2aa2aa2"
down_revision: str | None = "z1z1z1z1z1z1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "portfolio_benchmark_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column("benchmark_company_id", sa.Integer(), nullable=True),
        sa.Column("ticker", sa.String(length=40), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("provider_name", sa.String(length=80), nullable=False),
        sa.Column("provider_symbol", sa.String(length=80), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["benchmark_company_id"], ["companies.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("portfolio_id", name="uq_portfolio_benchmark_configs_portfolio"),
    )
    op.create_index(
        op.f("ix_portfolio_benchmark_configs_benchmark_company_id"),
        "portfolio_benchmark_configs",
        ["benchmark_company_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_portfolio_benchmark_configs_portfolio_id"),
        "portfolio_benchmark_configs",
        ["portfolio_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_portfolio_benchmark_configs_ticker"),
        "portfolio_benchmark_configs",
        ["ticker"],
        unique=False,
    )

    op.create_table(
        "fx_rate_observations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("base_currency", sa.String(length=10), nullable=False),
        sa.Column("quote_currency", sa.String(length=10), nullable=False),
        sa.Column("rate", sa.Numeric(precision=24, scale=10), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("provider_name", sa.String(length=80), nullable=False),
        sa.Column("provider_symbol", sa.String(length=80), nullable=True),
        sa.Column("source_url", sa.String(length=1000), nullable=True),
        sa.Column("source_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "base_currency",
            "quote_currency",
            "as_of_date",
            "provider_name",
            name="uq_fx_rate_observation_source_date",
        ),
    )
    op.create_index(op.f("ix_fx_rate_observations_as_of_date"), "fx_rate_observations", ["as_of_date"], unique=False)
    op.create_index(op.f("ix_fx_rate_observations_base_currency"), "fx_rate_observations", ["base_currency"], unique=False)
    op.create_index(op.f("ix_fx_rate_observations_provider_name"), "fx_rate_observations", ["provider_name"], unique=False)
    op.create_index(op.f("ix_fx_rate_observations_quote_currency"), "fx_rate_observations", ["quote_currency"], unique=False)

    op.add_column("portfolio_snapshots", sa.Column("total_portfolio_value", sa.Numeric(20, 6), nullable=True))
    op.add_column("portfolio_snapshots", sa.Column("base_currency", sa.String(10), nullable=True))
    op.add_column(
        "portfolio_snapshots",
        sa.Column("calculation_status", sa.String(30), server_default="not_available", nullable=False),
    )
    op.add_column("portfolio_snapshots", sa.Column("holdings_count", sa.Integer(), server_default="0", nullable=False))
    op.add_column("portfolio_snapshots", sa.Column("priced_holdings_count", sa.Integer(), server_default="0", nullable=False))
    op.add_column(
        "portfolio_snapshots",
        sa.Column("missing_price_tickers_json", sa.JSON(), server_default=sa.text("'[]'::json"), nullable=False),
    )
    op.add_column(
        "portfolio_snapshots",
        sa.Column("missing_fx_pairs_json", sa.JSON(), server_default=sa.text("'[]'::json"), nullable=False),
    )
    op.create_unique_constraint(
        "uq_portfolio_snapshots_portfolio_date",
        "portfolio_snapshots",
        ["portfolio_id", "snapshot_date"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_portfolio_snapshots_portfolio_date", "portfolio_snapshots", type_="unique")
    op.drop_column("portfolio_snapshots", "missing_fx_pairs_json")
    op.drop_column("portfolio_snapshots", "missing_price_tickers_json")
    op.drop_column("portfolio_snapshots", "priced_holdings_count")
    op.drop_column("portfolio_snapshots", "holdings_count")
    op.drop_column("portfolio_snapshots", "calculation_status")
    op.drop_column("portfolio_snapshots", "base_currency")
    op.drop_column("portfolio_snapshots", "total_portfolio_value")
    op.drop_index(op.f("ix_fx_rate_observations_quote_currency"), table_name="fx_rate_observations")
    op.drop_index(op.f("ix_fx_rate_observations_provider_name"), table_name="fx_rate_observations")
    op.drop_index(op.f("ix_fx_rate_observations_base_currency"), table_name="fx_rate_observations")
    op.drop_index(op.f("ix_fx_rate_observations_as_of_date"), table_name="fx_rate_observations")
    op.drop_table("fx_rate_observations")
    op.drop_index(op.f("ix_portfolio_benchmark_configs_ticker"), table_name="portfolio_benchmark_configs")
    op.drop_index(op.f("ix_portfolio_benchmark_configs_portfolio_id"), table_name="portfolio_benchmark_configs")
    op.drop_index(op.f("ix_portfolio_benchmark_configs_benchmark_company_id"), table_name="portfolio_benchmark_configs")
    op.drop_table("portfolio_benchmark_configs")
