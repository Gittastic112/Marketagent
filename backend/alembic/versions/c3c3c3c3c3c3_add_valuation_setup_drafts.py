"""add valuation setup drafts

Revision ID: c3c3c3c3c3c3
Revises: b2b2b2b2b2b2
Create Date: 2026-07-20 09:00:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c3c3c3c3c3c3"
down_revision: str | Sequence[str] | None = "b2b2b2b2b2b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "valuation_setup_drafts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("promoted_model_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="draft"),
        sa.Column("industry_name", sa.String(length=120), nullable=True),
        sa.Column("assumptions_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("provenance_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("source_metadata_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("warnings_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("reviewed_fields_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("edited_fields_json", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["promoted_model_id"], ["valuation_models.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_valuation_setup_drafts_user_id", "valuation_setup_drafts", ["user_id"])
    op.create_index("ix_valuation_setup_drafts_company_id", "valuation_setup_drafts", ["company_id"])
    op.create_index("ix_valuation_setup_drafts_status", "valuation_setup_drafts", ["status"])


def downgrade() -> None:
    op.drop_index("ix_valuation_setup_drafts_status", table_name="valuation_setup_drafts")
    op.drop_index("ix_valuation_setup_drafts_company_id", table_name="valuation_setup_drafts")
    op.drop_index("ix_valuation_setup_drafts_user_id", table_name="valuation_setup_drafts")
    op.drop_table("valuation_setup_drafts")
