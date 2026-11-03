"""add sourced target comparability profiles to peer sets

Revision ID: m4m4m4m4m4m4
Revises: l3l3l3l3l3l3
Create Date: 2026-09-03
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "m4m4m4m4m4m4"
down_revision: str | None = "l3l3l3l3l3l3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _target_columns(parent_column: str, parent_table: str) -> list[sa.Column]:
    return [
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(parent_column, sa.Integer(), nullable=False),
        sa.Column("source_name", sa.String(length=160), nullable=False),
        sa.Column("source_url", sa.String(length=2048), nullable=False),
        sa.Column("source_as_of", sa.Date(), nullable=False),
        sa.Column("claim_type", sa.String(length=30), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("country", sa.String(length=120), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("fiscal_period_end", sa.Date(), nullable=True),
        sa.Column("accounting_standard", sa.String(length=40), nullable=True),
        sa.Column("market_cap", sa.Float(), nullable=True),
        sa.Column("revenue_growth_pct", sa.Float(), nullable=True),
        sa.Column("ebitda_margin_pct", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint([parent_column], [f"{parent_table}.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(parent_column, name=f"uq_{parent_table}_target_profile"),
    ]


def upgrade() -> None:
    op.add_column(
        "peer_valuation_sets",
        sa.Column("target_context_json", sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
    )
    op.add_column(
        "peer_valuation_set_revisions",
        sa.Column("target_context_json", sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
    )
    op.create_table(
        "peer_valuation_target_profiles",
        *_target_columns("peer_set_id", "peer_valuation_sets"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_peer_valuation_target_profiles_peer_set_id",
        "peer_valuation_target_profiles",
        ["peer_set_id"],
    )
    op.create_table(
        "peer_valuation_revision_target_profiles",
        *_target_columns("revision_id", "peer_valuation_set_revisions"),
    )
    op.create_index(
        "ix_peer_valuation_revision_target_profiles_revision_id",
        "peer_valuation_revision_target_profiles",
        ["revision_id"],
    )


def downgrade() -> None:
    op.drop_table("peer_valuation_revision_target_profiles")
    op.drop_table("peer_valuation_target_profiles")
    op.drop_column("peer_valuation_set_revisions", "target_context_json")
    op.drop_column("peer_valuation_sets", "target_context_json")
