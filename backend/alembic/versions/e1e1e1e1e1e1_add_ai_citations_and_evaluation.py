"""Add AI citations, evaluation, and review notes.

Revision ID: e1e1e1e1e1e1
Revises: d0d0d0d0d0d0
Create Date: 2026-07-31
"""

from alembic import op
import sqlalchemy as sa


revision = "e1e1e1e1e1e1"
down_revision = "d0d0d0d0d0d0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ai_outputs",
        sa.Column("citations_json", sa.JSON(), server_default=sa.text("'[]'::json"), nullable=False),
    )
    op.add_column(
        "ai_outputs",
        sa.Column(
            "citation_validation_status",
            sa.String(length=30),
            server_default="not_evaluated",
            nullable=False,
        ),
    )
    op.add_column("ai_outputs", sa.Column("evaluation_json", sa.JSON(), nullable=True))
    op.add_column("ai_outputs", sa.Column("review_notes", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("ai_outputs", "review_notes")
    op.drop_column("ai_outputs", "evaluation_json")
    op.drop_column("ai_outputs", "citation_validation_status")
    op.drop_column("ai_outputs", "citations_json")
