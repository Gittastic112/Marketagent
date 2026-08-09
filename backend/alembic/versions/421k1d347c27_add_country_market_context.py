"""add_country_market_context

Revision ID: 421k1d347c27
Revises: 420j1d347c26
Create Date: 2026-06-18 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "421k1d347c27"
down_revision: str | Sequence[str] | None = "420j1d347c26"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "country_market_context",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("market", sa.String(length=10), nullable=False),
        sa.Column("country", sa.String(length=120), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("risk_free_rate", sa.Float(), nullable=True),
        sa.Column("risk_free_rate_source", sa.String(length=255), nullable=True),
        sa.Column("equity_risk_premium", sa.Float(), nullable=True),
        sa.Column("country_risk_premium", sa.Float(), nullable=True),
        sa.Column("inflation_rate", sa.Float(), nullable=True),
        sa.Column("fx_rate_to_usd", sa.Float(), nullable=True),
        sa.Column("as_of_date", sa.Date(), nullable=True),
        sa.Column("is_manual", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("market", name="uq_country_market_context_market"),
    )
    op.create_index(op.f("ix_country_market_context_market"), "country_market_context", ["market"], unique=False)
    op.create_index(op.f("ix_country_market_context_country"), "country_market_context", ["country"], unique=False)
    op.create_index(op.f("ix_country_market_context_currency"), "country_market_context", ["currency"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_country_market_context_currency"), table_name="country_market_context")
    op.drop_index(op.f("ix_country_market_context_country"), table_name="country_market_context")
    op.drop_index(op.f("ix_country_market_context_market"), table_name="country_market_context")
    op.drop_table("country_market_context")
