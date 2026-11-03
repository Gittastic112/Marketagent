"""add reviewed peer valuation set fields

Revision ID: j1j1j1j1j1j1
Revises: i0i0i0i0i0i0
Create Date: 2026-08-26
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "j1j1j1j1j1j1"
down_revision: str | None = "i0i0i0i0i0i0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "peer_valuation_sets",
        sa.Column("aggregation_method", sa.String(length=20), server_default="median", nullable=False),
    )
    op.add_column(
        "peer_valuation_sets",
        sa.Column("review_status", sa.String(length=20), server_default="draft", nullable=False),
    )
    op.add_column(
        "peer_valuation_sets",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "peer_valuation_sets",
        sa.Column("reviewed_by_user_id", sa.String(), nullable=True),
    )
    op.create_foreign_key(
        "fk_peer_valuation_sets_reviewed_by_user_id_users",
        "peer_valuation_sets",
        "users",
        ["reviewed_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_peer_valuation_sets_review_status",
        "peer_valuation_sets",
        ["review_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_peer_valuation_sets_review_status", table_name="peer_valuation_sets")
    op.drop_constraint(
        "fk_peer_valuation_sets_reviewed_by_user_id_users",
        "peer_valuation_sets",
        type_="foreignkey",
    )
    op.drop_column("peer_valuation_sets", "reviewed_by_user_id")
    op.drop_column("peer_valuation_sets", "reviewed_at")
    op.drop_column("peer_valuation_sets", "review_status")
    op.drop_column("peer_valuation_sets", "aggregation_method")
