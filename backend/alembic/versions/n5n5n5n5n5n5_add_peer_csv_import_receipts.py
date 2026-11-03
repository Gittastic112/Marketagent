"""add owner-scoped peer CSV import receipts

Revision ID: n5n5n5n5n5n5
Revises: m4m4m4m4m4m4
Create Date: 2026-09-04
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "n5n5n5n5n5n5"
down_revision: str | None = "m4m4m4m4m4m4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "peer_valuation_sets",
        sa.Column("import_sha256", sa.String(length=64), nullable=True),
    )
    op.create_unique_constraint(
        "uq_peer_valuation_sets_owner_company_import_sha256",
        "peer_valuation_sets",
        ["user_id", "company_id", "import_sha256"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_peer_valuation_sets_owner_company_import_sha256",
        "peer_valuation_sets",
        type_="unique",
    )
    op.drop_column("peer_valuation_sets", "import_sha256")
