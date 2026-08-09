"""Add request correlation to processing runs.

Revision ID: c9c9c9c9c9c9
Revises: b8b8b8b8b8b8
Create Date: 2026-07-26
"""

from alembic import op
import sqlalchemy as sa


revision = "c9c9c9c9c9c9"
down_revision = "b8b8b8b8b8b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "processing_runs",
        sa.Column("request_id", sa.String(length=36), nullable=True),
    )
    op.create_index(
        "ix_processing_runs_request_id",
        "processing_runs",
        ["request_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_processing_runs_request_id", table_name="processing_runs")
    op.drop_column("processing_runs", "request_id")
