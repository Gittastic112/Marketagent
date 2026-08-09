"""add_company_market_identity

Revision ID: 418h1d347c24
Revises: 417g1d347c23
Create Date: 2026-06-17 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "418h1d347c24"
down_revision: str | Sequence[str] | None = "417g1d347c23"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index(op.f("ix_companies_ticker"), table_name="companies")

    op.add_column("companies", sa.Column("market", sa.String(length=10), nullable=False, server_default="US"))
    op.add_column("companies", sa.Column("primary_exchange", sa.String(length=20), nullable=True))
    op.add_column("companies", sa.Column("local_symbol", sa.String(length=40), nullable=True))
    op.add_column("companies", sa.Column("isin", sa.String(length=20), nullable=True))
    op.add_column("companies", sa.Column("figi", sa.String(length=32), nullable=True))
    op.add_column("companies", sa.Column("regulatory_id", sa.String(length=40), nullable=True))
    op.add_column("companies", sa.Column("regulatory_id_type", sa.String(length=40), nullable=True))

    op.execute("UPDATE companies SET ticker = UPPER(ticker)")
    op.execute("UPDATE companies SET local_symbol = UPPER(ticker) WHERE local_symbol IS NULL")
    op.execute("UPDATE companies SET primary_exchange = UPPER(exchange) WHERE primary_exchange IS NULL AND exchange IS NOT NULL")
    op.execute("UPDATE companies SET exchange = UPPER(exchange) WHERE exchange IS NOT NULL")
    op.execute("UPDATE companies SET currency = 'USD' WHERE currency IS NULL")
    op.execute("UPDATE companies SET country = 'United States' WHERE country IS NULL")
    op.execute("UPDATE companies SET regulatory_id = cik WHERE regulatory_id IS NULL AND cik IS NOT NULL")

    op.create_index(op.f("ix_companies_ticker"), "companies", ["ticker"], unique=False)
    op.create_index(op.f("ix_companies_market"), "companies", ["market"], unique=False)
    op.create_index(op.f("ix_companies_primary_exchange"), "companies", ["primary_exchange"], unique=False)
    op.create_index(op.f("ix_companies_local_symbol"), "companies", ["local_symbol"], unique=False)
    op.create_index(op.f("ix_companies_isin"), "companies", ["isin"], unique=False)
    op.create_index(op.f("ix_companies_figi"), "companies", ["figi"], unique=False)
    op.create_index(op.f("ix_companies_regulatory_id"), "companies", ["regulatory_id"], unique=False)
    op.create_unique_constraint(
        "uq_companies_market_exchange_symbol",
        "companies",
        ["market", "primary_exchange", "local_symbol"],
    )
    op.alter_column("companies", "market", server_default=None)


def downgrade() -> None:
    op.drop_constraint("uq_companies_market_exchange_symbol", "companies", type_="unique")
    op.drop_index(op.f("ix_companies_regulatory_id"), table_name="companies")
    op.drop_index(op.f("ix_companies_figi"), table_name="companies")
    op.drop_index(op.f("ix_companies_isin"), table_name="companies")
    op.drop_index(op.f("ix_companies_local_symbol"), table_name="companies")
    op.drop_index(op.f("ix_companies_primary_exchange"), table_name="companies")
    op.drop_index(op.f("ix_companies_market"), table_name="companies")
    op.drop_index(op.f("ix_companies_ticker"), table_name="companies")

    op.drop_column("companies", "regulatory_id_type")
    op.drop_column("companies", "regulatory_id")
    op.drop_column("companies", "figi")
    op.drop_column("companies", "isin")
    op.drop_column("companies", "local_symbol")
    op.drop_column("companies", "primary_exchange")
    op.drop_column("companies", "market")

    op.create_index(op.f("ix_companies_ticker"), "companies", ["ticker"], unique=True)
