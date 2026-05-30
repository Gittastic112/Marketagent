"""create processing runs

Revision ID: 20260524_0004
Revises: 20260524_0003
Create Date: 2026-05-24
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260524_0004"
down_revision: str | Sequence[str] | None = "20260524_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "processing_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_type", sa.String(length=80), nullable=False),
        sa.Column("source_type", sa.String(length=80), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("fetched_count", sa.Integer(), nullable=False),
        sa.Column("created_count", sa.Integer(), nullable=False),
        sa.Column("skipped_duplicate_count", sa.Integer(), nullable=False),
        sa.Column("error_count", sa.Integer(), nullable=False),
        sa.Column("error_details_json", sa.JSON(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_processing_runs_run_type", "processing_runs", ["run_type"])
    op.create_index("ix_processing_runs_source_type", "processing_runs", ["source_type"])
    op.create_index("ix_processing_runs_status", "processing_runs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_processing_runs_status", table_name="processing_runs")
    op.drop_index("ix_processing_runs_source_type", table_name="processing_runs")
    op.drop_index("ix_processing_runs_run_type", table_name="processing_runs")
    op.drop_table("processing_runs")
