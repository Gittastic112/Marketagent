"""add company classification

Revision ID: 20260524_0009
Revises: 20260524_0008
Create Date: 2026-05-26
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260524_0009"
down_revision: str | Sequence[str] | None = "20260524_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("country", sa.String(length=120), nullable=True))
    op.add_column("companies", sa.Column("region", sa.String(length=120), nullable=True))
    op.add_column("companies", sa.Column("currency", sa.String(length=10), nullable=True))
    op.add_column("companies", sa.Column("asset_type", sa.String(length=80), nullable=True))
    op.add_column("companies", sa.Column("security_type", sa.String(length=80), nullable=True))
    op.add_column("companies", sa.Column("market_cap_category", sa.String(length=80), nullable=True))
    op.add_column("companies", sa.Column("is_etf", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column("companies", sa.Column("etf_provider", sa.String(length=120), nullable=True))


def downgrade() -> None:
    op.drop_column("companies", "etf_provider")
    op.drop_column("companies", "is_etf")
    op.drop_column("companies", "market_cap_category")
    op.drop_column("companies", "security_type")
    op.drop_column("companies", "asset_type")
    op.drop_column("companies", "currency")
    op.drop_column("companies", "region")
    op.drop_column("companies", "country")
