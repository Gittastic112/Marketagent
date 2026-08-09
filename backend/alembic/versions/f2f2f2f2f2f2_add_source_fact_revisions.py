"""Add point-in-time source fact revisions.

Revision ID: f2f2f2f2f2f2
Revises: e1e1e1e1e1e1
Create Date: 2026-07-31
"""

from alembic import op
import sqlalchemy as sa


revision = "f2f2f2f2f2f2"
down_revision = "e1e1e1e1e1e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "source_fact_revisions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("raw_document_id", sa.Integer(), nullable=False),
        sa.Column("financial_candidate_id", sa.Integer(), nullable=False),
        sa.Column("fact_key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=100), nullable=True),
        sa.Column("period_type", sa.String(length=40), nullable=False),
        sa.Column("effective_at", sa.Date(), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("claim_type", sa.String(length=30), server_default="Fact", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["raw_document_id"], ["raw_documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["financial_candidate_id"],
            ["financial_extraction_candidates.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("financial_candidate_id", name="uq_source_fact_revision_candidate"),
    )
    for column in (
        "company_id",
        "raw_document_id",
        "financial_candidate_id",
        "fact_key",
        "period_type",
        "effective_at",
        "observed_at",
        "superseded_at",
    ):
        op.create_index(f"ix_source_fact_revisions_{column}", "source_fact_revisions", [column])


def downgrade() -> None:
    op.drop_table("source_fact_revisions")
