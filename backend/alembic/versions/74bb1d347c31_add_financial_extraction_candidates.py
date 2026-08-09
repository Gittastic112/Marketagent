"""add financial extraction candidates

Revision ID: 74bb1d347c31
Revises: 73aa1d347c30
Create Date: 2026-06-20 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "74bb1d347c31"
down_revision = "73aa1d347c30"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "financial_extraction_candidates",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("raw_document_id", sa.Integer(), nullable=False),
        sa.Column("metric_code", sa.String(length=80), nullable=False),
        sa.Column("reported_label", sa.String(length=255), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(), nullable=True),
        sa.Column("fiscal_year", sa.Integer(), nullable=True),
        sa.Column("period_type", sa.String(length=40), nullable=False),
        sa.Column("source_text", sa.String(), nullable=False),
        sa.Column("extraction_method", sa.String(length=80), nullable=False),
        sa.Column("confidence_label", sa.String(length=40), nullable=False),
        sa.Column("review_status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["raw_document_id"], ["raw_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_financial_extraction_candidates_company_id"), "financial_extraction_candidates", ["company_id"], unique=False)
    op.create_index(op.f("ix_financial_extraction_candidates_fiscal_year"), "financial_extraction_candidates", ["fiscal_year"], unique=False)
    op.create_index(op.f("ix_financial_extraction_candidates_metric_code"), "financial_extraction_candidates", ["metric_code"], unique=False)
    op.create_index(op.f("ix_financial_extraction_candidates_period_type"), "financial_extraction_candidates", ["period_type"], unique=False)
    op.create_index(op.f("ix_financial_extraction_candidates_raw_document_id"), "financial_extraction_candidates", ["raw_document_id"], unique=False)
    op.create_index(op.f("ix_financial_extraction_candidates_review_status"), "financial_extraction_candidates", ["review_status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_financial_extraction_candidates_review_status"), table_name="financial_extraction_candidates")
    op.drop_index(op.f("ix_financial_extraction_candidates_raw_document_id"), table_name="financial_extraction_candidates")
    op.drop_index(op.f("ix_financial_extraction_candidates_period_type"), table_name="financial_extraction_candidates")
    op.drop_index(op.f("ix_financial_extraction_candidates_metric_code"), table_name="financial_extraction_candidates")
    op.drop_index(op.f("ix_financial_extraction_candidates_fiscal_year"), table_name="financial_extraction_candidates")
    op.drop_index(op.f("ix_financial_extraction_candidates_company_id"), table_name="financial_extraction_candidates")
    op.drop_table("financial_extraction_candidates")
