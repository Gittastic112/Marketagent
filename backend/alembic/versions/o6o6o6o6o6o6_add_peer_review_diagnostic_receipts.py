"""add peer review diagnostic receipts

Revision ID: o6o6o6o6o6o6
Revises: n5n5n5n5n5n5
Create Date: 2026-09-05
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "o6o6o6o6o6o6"
down_revision: str | None = "n5n5n5n5n5n5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for table_name in ("peer_valuation_sets", "peer_valuation_set_revisions"):
        op.add_column(
            table_name,
            sa.Column("review_diagnostics_sha256", sa.String(length=64), nullable=True),
        )
        op.add_column(
            table_name,
            sa.Column("review_warning_codes_json", sa.JSON(), nullable=True),
        )
        op.add_column(
            table_name,
            sa.Column("review_diagnostics_as_of", sa.Date(), nullable=True),
        )


def downgrade() -> None:
    for table_name in ("peer_valuation_set_revisions", "peer_valuation_sets"):
        op.drop_column(table_name, "review_diagnostics_as_of")
        op.drop_column(table_name, "review_warning_codes_json")
        op.drop_column(table_name, "review_diagnostics_sha256")
