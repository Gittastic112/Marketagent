"""create portfolio tables

Revision ID: 20260524_0008
Revises: 20260524_0007
Create Date: 2026-05-26
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260524_0008"
down_revision: str | Sequence[str] | None = "20260524_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "portfolios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("base_currency", sa.String(length=10), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_portfolios_name"), "portfolios", ["name"], unique=False)

    op.create_table(
        "portfolio_holdings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("ticker", sa.String(length=20), nullable=False),
        sa.Column("quantity", sa.Numeric(20, 6), nullable=False),
        sa.Column("average_cost", sa.Numeric(20, 6), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_portfolio_holdings_company_id"), "portfolio_holdings", ["company_id"], unique=False)
    op.create_index(op.f("ix_portfolio_holdings_portfolio_id"), "portfolio_holdings", ["portfolio_id"], unique=False)
    op.create_index(op.f("ix_portfolio_holdings_ticker"), "portfolio_holdings", ["ticker"], unique=False)

    op.create_table(
        "portfolio_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("ticker", sa.String(length=20), nullable=False),
        sa.Column("transaction_type", sa.String(length=40), nullable=False),
        sa.Column("quantity", sa.Numeric(20, 6), nullable=False),
        sa.Column("price", sa.Numeric(20, 6), nullable=False),
        sa.Column("fees", sa.Numeric(20, 6), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_portfolio_transactions_company_id"), "portfolio_transactions", ["company_id"], unique=False)
    op.create_index(op.f("ix_portfolio_transactions_portfolio_id"), "portfolio_transactions", ["portfolio_id"], unique=False)
    op.create_index(op.f("ix_portfolio_transactions_ticker"), "portfolio_transactions", ["ticker"], unique=False)
    op.create_index(
        op.f("ix_portfolio_transactions_transaction_date"),
        "portfolio_transactions",
        ["transaction_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_portfolio_transactions_transaction_type"),
        "portfolio_transactions",
        ["transaction_type"],
        unique=False,
    )

    op.create_table(
        "portfolio_cash_balances",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("amount", sa.Numeric(20, 6), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_portfolio_cash_balances_portfolio_id"),
        "portfolio_cash_balances",
        ["portfolio_id"],
        unique=False,
    )

    op.create_table(
        "portfolio_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("total_market_value", sa.Numeric(20, 6), nullable=True),
        sa.Column("total_cost_basis", sa.Numeric(20, 6), nullable=True),
        sa.Column("total_cash", sa.Numeric(20, 6), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_portfolio_snapshots_portfolio_id"), "portfolio_snapshots", ["portfolio_id"], unique=False)
    op.create_index(op.f("ix_portfolio_snapshots_snapshot_date"), "portfolio_snapshots", ["snapshot_date"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_portfolio_snapshots_snapshot_date"), table_name="portfolio_snapshots")
    op.drop_index(op.f("ix_portfolio_snapshots_portfolio_id"), table_name="portfolio_snapshots")
    op.drop_table("portfolio_snapshots")

    op.drop_index(op.f("ix_portfolio_cash_balances_portfolio_id"), table_name="portfolio_cash_balances")
    op.drop_table("portfolio_cash_balances")

    op.drop_index(op.f("ix_portfolio_transactions_transaction_type"), table_name="portfolio_transactions")
    op.drop_index(op.f("ix_portfolio_transactions_transaction_date"), table_name="portfolio_transactions")
    op.drop_index(op.f("ix_portfolio_transactions_ticker"), table_name="portfolio_transactions")
    op.drop_index(op.f("ix_portfolio_transactions_portfolio_id"), table_name="portfolio_transactions")
    op.drop_index(op.f("ix_portfolio_transactions_company_id"), table_name="portfolio_transactions")
    op.drop_table("portfolio_transactions")

    op.drop_index(op.f("ix_portfolio_holdings_ticker"), table_name="portfolio_holdings")
    op.drop_index(op.f("ix_portfolio_holdings_portfolio_id"), table_name="portfolio_holdings")
    op.drop_index(op.f("ix_portfolio_holdings_company_id"), table_name="portfolio_holdings")
    op.drop_table("portfolio_holdings")

    op.drop_index(op.f("ix_portfolios_name"), table_name="portfolios")
    op.drop_table("portfolios")
