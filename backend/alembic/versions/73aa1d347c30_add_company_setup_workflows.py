"""add company setup workflows

Revision ID: 73aa1d347c30
Revises: 72fa829402a4
Create Date: 2026-06-20 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "73aa1d347c30"
down_revision = "72fa829402a4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "company_setup_workflows",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("current_step", sa.String(length=80), nullable=False),
        sa.Column("identity_status", sa.String(length=40), nullable=False),
        sa.Column("source_status", sa.String(length=40), nullable=False),
        sa.Column("filing_status", sa.String(length=40), nullable=False),
        sa.Column("financial_extraction_status", sa.String(length=40), nullable=False),
        sa.Column("industry_mapping_status", sa.String(length=40), nullable=False),
        sa.Column("valuation_readiness_status", sa.String(length=40), nullable=False),
        sa.Column("security_review_status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id"),
    )
    op.create_index(op.f("ix_company_setup_workflows_company_id"), "company_setup_workflows", ["company_id"], unique=True)
    op.create_index(op.f("ix_company_setup_workflows_current_step"), "company_setup_workflows", ["current_step"], unique=False)
    op.create_index(op.f("ix_company_setup_workflows_identity_status"), "company_setup_workflows", ["identity_status"], unique=False)
    op.create_index(op.f("ix_company_setup_workflows_source_status"), "company_setup_workflows", ["source_status"], unique=False)
    op.create_index(op.f("ix_company_setup_workflows_filing_status"), "company_setup_workflows", ["filing_status"], unique=False)
    op.create_index(op.f("ix_company_setup_workflows_financial_extraction_status"), "company_setup_workflows", ["financial_extraction_status"], unique=False)
    op.create_index(op.f("ix_company_setup_workflows_industry_mapping_status"), "company_setup_workflows", ["industry_mapping_status"], unique=False)
    op.create_index(op.f("ix_company_setup_workflows_valuation_readiness_status"), "company_setup_workflows", ["valuation_readiness_status"], unique=False)
    op.create_index(op.f("ix_company_setup_workflows_security_review_status"), "company_setup_workflows", ["security_review_status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_company_setup_workflows_security_review_status"), table_name="company_setup_workflows")
    op.drop_index(op.f("ix_company_setup_workflows_valuation_readiness_status"), table_name="company_setup_workflows")
    op.drop_index(op.f("ix_company_setup_workflows_industry_mapping_status"), table_name="company_setup_workflows")
    op.drop_index(op.f("ix_company_setup_workflows_financial_extraction_status"), table_name="company_setup_workflows")
    op.drop_index(op.f("ix_company_setup_workflows_filing_status"), table_name="company_setup_workflows")
    op.drop_index(op.f("ix_company_setup_workflows_source_status"), table_name="company_setup_workflows")
    op.drop_index(op.f("ix_company_setup_workflows_identity_status"), table_name="company_setup_workflows")
    op.drop_index(op.f("ix_company_setup_workflows_current_step"), table_name="company_setup_workflows")
    op.drop_index(op.f("ix_company_setup_workflows_company_id"), table_name="company_setup_workflows")
    op.drop_table("company_setup_workflows")
