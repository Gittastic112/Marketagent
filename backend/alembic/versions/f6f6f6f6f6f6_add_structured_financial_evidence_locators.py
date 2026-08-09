"""add structured financial evidence locators

Revision ID: f6f6f6f6f6f6
Revises: e5e5e5e5e5e5
Create Date: 2026-07-25 10:00:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f6f6f6f6f6f6"
down_revision: str | Sequence[str] | None = "e5e5e5e5e5e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "financial_extraction_candidates",
        sa.Column("source_table_name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "financial_extraction_candidates",
        sa.Column("source_row_label", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "financial_extraction_candidates",
        sa.Column("source_column_label", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "financial_extraction_candidates",
        sa.Column("source_cell_reference", sa.String(length=40), nullable=True),
    )
    op.add_column(
        "financial_extraction_candidates",
        sa.Column("source_locator_json", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("financial_extraction_candidates", "source_locator_json")
    op.drop_column("financial_extraction_candidates", "source_cell_reference")
    op.drop_column("financial_extraction_candidates", "source_column_label")
    op.drop_column("financial_extraction_candidates", "source_row_label")
    op.drop_column("financial_extraction_candidates", "source_table_name")
