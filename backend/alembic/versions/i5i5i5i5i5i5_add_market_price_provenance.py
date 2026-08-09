"""Add market-price provider provenance.

Revision ID: i5i5i5i5i5i5
Revises: h4h4h4h4h4h4
Create Date: 2026-08-01
"""

import sqlalchemy as sa
from alembic import op


revision = "i5i5i5i5i5i5"
down_revision = "h4h4h4h4h4h4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("market_prices", sa.Column("provider_name", sa.String(length=50), nullable=True))
    op.add_column("market_prices", sa.Column("provider_symbol", sa.String(length=50), nullable=True))
    op.add_column("market_prices", sa.Column("market", sa.String(length=20), nullable=True))
    op.add_column("market_prices", sa.Column("exchange", sa.String(length=30), nullable=True))
    op.add_column("market_prices", sa.Column("source_timestamp", sa.DateTime(timezone=True), nullable=True))
    op.add_column("market_prices", sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("market_prices", sa.Column("price_type", sa.String(length=30), nullable=True))
    op.add_column("market_prices", sa.Column("delay_minutes", sa.Integer(), nullable=True))
    op.add_column("market_prices", sa.Column("adjustment_state", sa.String(length=30), nullable=True))
    op.add_column("market_prices", sa.Column("warnings_json", sa.JSON(), nullable=True))
    op.execute(
        "UPDATE market_prices SET provider_name = 'legacy_unknown', observed_at = created_at, "
        "price_type = 'unknown', adjustment_state = 'unknown', warnings_json = '[]'::json "
        "WHERE provider_name IS NULL"
    )
    op.alter_column("market_prices", "provider_name", nullable=False, server_default="manual")
    op.alter_column("market_prices", "observed_at", nullable=False, server_default=sa.func.now())
    op.alter_column("market_prices", "price_type", nullable=False, server_default="manual")
    op.alter_column("market_prices", "adjustment_state", nullable=False, server_default="not_applicable")
    op.alter_column("market_prices", "warnings_json", nullable=False, server_default=sa.text("'[]'::json"))
    op.create_index("ix_market_prices_provider_name", "market_prices", ["provider_name"])

    op.add_column("company_market_data", sa.Column("provider_name", sa.String(length=50), nullable=True))
    op.add_column("company_market_data", sa.Column("provider_symbol", sa.String(length=50), nullable=True))
    op.add_column("company_market_data", sa.Column("source_timestamp", sa.DateTime(timezone=True), nullable=True))
    op.add_column("company_market_data", sa.Column("observed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("company_market_data", sa.Column("price_type", sa.String(length=30), nullable=True))
    op.add_column("company_market_data", sa.Column("delay_minutes", sa.Integer(), nullable=True))
    op.add_column("company_market_data", sa.Column("adjustment_state", sa.String(length=30), nullable=True))
    op.add_column("company_market_data", sa.Column("warnings_json", sa.JSON(), nullable=True))
    op.execute(
        "UPDATE company_market_data SET provider_name = 'legacy_unknown', observed_at = last_updated, "
        "price_type = 'unknown', adjustment_state = 'unknown', warnings_json = '[]'::json "
        "WHERE provider_name IS NULL"
    )
    op.alter_column("company_market_data", "provider_name", nullable=False, server_default="legacy_unknown")
    op.alter_column("company_market_data", "observed_at", nullable=False, server_default=sa.func.now())
    op.alter_column("company_market_data", "price_type", nullable=False, server_default="unknown")
    op.alter_column("company_market_data", "adjustment_state", nullable=False, server_default="unknown")
    op.alter_column("company_market_data", "warnings_json", nullable=False, server_default=sa.text("'[]'::json"))


def downgrade() -> None:
    for column in (
        "warnings_json",
        "adjustment_state",
        "delay_minutes",
        "price_type",
        "observed_at",
        "source_timestamp",
        "provider_symbol",
        "provider_name",
    ):
        op.drop_column("company_market_data", column)

    op.drop_index("ix_market_prices_provider_name", table_name="market_prices")
    for column in (
        "warnings_json",
        "adjustment_state",
        "delay_minutes",
        "price_type",
        "observed_at",
        "source_timestamp",
        "exchange",
        "market",
        "provider_symbol",
        "provider_name",
    ):
        op.drop_column("market_prices", column)
