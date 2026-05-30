"""add market prices

Revision ID: 20260528_0010
Revises: 20260524_0009
Create Date: 2026-05-28
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260528_0010"
down_revision: str | Sequence[str] | None = "20260524_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "market_prices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("ticker", sa.String(length=20), nullable=False),
        sa.Column("price", sa.Numeric(20, 6), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_market_prices_company_id"), "market_prices", ["company_id"], unique=False)
    op.create_index(op.f("ix_market_prices_ticker"), "market_prices", ["ticker"], unique=False)
    op.create_index(op.f("ix_market_prices_as_of_date"), "market_prices", ["as_of_date"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_market_prices_as_of_date"), table_name="market_prices")
    op.drop_index(op.f("ix_market_prices_ticker"), table_name="market_prices")
    op.drop_index(op.f("ix_market_prices_company_id"), table_name="market_prices")
    op.drop_table("market_prices")
