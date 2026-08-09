"""Add exact event evidence references.

Revision ID: d0d0d0d0d0d0
Revises: c9c9c9c9c9c9
Create Date: 2026-07-31
"""

from alembic import op
import sqlalchemy as sa


revision = "d0d0d0d0d0d0"
down_revision = "c9c9c9c9c9c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_evidence_references",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("raw_document_id", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.String(length=255), nullable=True),
        sa.Column("locator_type", sa.String(length=30), nullable=False),
        sa.Column("source_page", sa.Integer(), nullable=True),
        sa.Column("source_section", sa.String(length=500), nullable=True),
        sa.Column("start_char", sa.Integer(), nullable=True),
        sa.Column("end_char", sa.Integer(), nullable=True),
        sa.Column("quote", sa.Text(), nullable=True),
        sa.Column("bounding_box_json", sa.JSON(), nullable=True),
        sa.Column("source_metadata_json", sa.JSON(), nullable=True),
        sa.Column("confidence_label", sa.String(length=20), server_default="high", nullable=False),
        sa.Column("origin", sa.String(length=30), server_default="manual_review", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("source_page IS NULL OR source_page > 0", name="ck_event_evidence_source_page_positive"),
        sa.CheckConstraint("start_char IS NULL OR start_char >= 0", name="ck_event_evidence_start_char_nonnegative"),
        sa.CheckConstraint("end_char IS NULL OR end_char > start_char", name="ck_event_evidence_char_range"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["raw_document_id"], ["raw_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_event_evidence_references_event_id", "event_evidence_references", ["event_id"])
    op.create_index("ix_event_evidence_references_raw_document_id", "event_evidence_references", ["raw_document_id"])
    op.create_index("ix_event_evidence_references_locator_type", "event_evidence_references", ["locator_type"])


def downgrade() -> None:
    op.drop_index("ix_event_evidence_references_locator_type", table_name="event_evidence_references")
    op.drop_index("ix_event_evidence_references_raw_document_id", table_name="event_evidence_references")
    op.drop_index("ix_event_evidence_references_event_id", table_name="event_evidence_references")
    op.drop_table("event_evidence_references")
