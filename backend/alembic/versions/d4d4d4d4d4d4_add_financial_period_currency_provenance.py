"""add financial period currency provenance

Revision ID: d4d4d4d4d4d4
Revises: c3c3c3c3c3c3
Create Date: 2026-07-22 09:00:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "d4d4d4d4d4d4"
down_revision: str | Sequence[str] | None = "c3c3c3c3c3c3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "financial_statement_periods",
        sa.Column("currency_source", sa.String(length=80), nullable=False, server_default="legacy_unknown"),
    )
    op.add_column(
        "financial_statement_periods",
        sa.Column("currency_confidence", sa.String(length=40), nullable=False, server_default="unknown"),
    )


def downgrade() -> None:
    op.drop_column("financial_statement_periods", "currency_confidence")
    op.drop_column("financial_statement_periods", "currency_source")
