"""Add revenue-weighted company industry mixes.

Revision ID: j6j6j6j6j6j6
Revises: i5i5i5i5i5i5
Create Date: 2026-08-01
"""

import sqlalchemy as sa
from alembic import op


revision = "j6j6j6j6j6j6"
down_revision = "i5i5i5i5i5i5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "company_industry_mixes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("basis", sa.String(length=40), nullable=False, server_default="revenue"),
        sa.Column("as_of_date", sa.Date(), nullable=True),
        sa.Column("source_document_id", sa.Integer(), nullable=True),
        sa.Column("notes", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_document_id"], ["raw_documents.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("company_id", name="uq_company_industry_mixes_company_id"),
    )
    op.create_index("ix_company_industry_mixes_company_id", "company_industry_mixes", ["company_id"])
    op.create_table(
        "company_industry_allocations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("mix_id", sa.Integer(), nullable=False),
        sa.Column("segment_name", sa.String(length=120), nullable=False),
        sa.Column("industry_name", sa.String(length=255), nullable=False),
        sa.Column("weight_percent", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("weight_percent > 0 AND weight_percent <= 100", name="ck_industry_weight_range"),
        sa.ForeignKeyConstraint(["mix_id"], ["company_industry_mixes.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("mix_id", "segment_name", name="uq_company_industry_allocation_segment"),
    )
    op.create_index("ix_company_industry_allocations_mix_id", "company_industry_allocations", ["mix_id"])
    op.create_index(
        "ix_company_industry_allocations_industry_name",
        "company_industry_allocations",
        ["industry_name"],
    )


def downgrade() -> None:
    op.drop_index("ix_company_industry_allocations_industry_name", table_name="company_industry_allocations")
    op.drop_index("ix_company_industry_allocations_mix_id", table_name="company_industry_allocations")
    op.drop_table("company_industry_allocations")
    op.drop_index("ix_company_industry_mixes_company_id", table_name="company_industry_mixes")
    op.drop_table("company_industry_mixes")
