"""add financial candidate evidence

Revision ID: e5e5e5e5e5e5
Revises: d4d4d4d4d4d4
Create Date: 2026-07-22 14:00:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "e5e5e5e5e5e5"
down_revision: str | Sequence[str] | None = "d4d4d4d4d4d4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "financial_extraction_candidates",
        sa.Column("source_line_number", sa.Integer(), nullable=True),
    )
    op.add_column(
        "financial_extraction_candidates",
        sa.Column("source_page", sa.Integer(), nullable=True),
    )
    op.add_column(
        "financial_extraction_candidates",
        sa.Column("source_section", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "financial_extraction_candidates",
        sa.Column("extraction_warnings", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("financial_extraction_candidates", "extraction_warnings")
    op.drop_column("financial_extraction_candidates", "source_section")
    op.drop_column("financial_extraction_candidates", "source_page")
    op.drop_column("financial_extraction_candidates", "source_line_number")
