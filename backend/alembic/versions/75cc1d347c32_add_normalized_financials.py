"""add normalized financials

Revision ID: 75cc1d347c32
Revises: 74bb1d347c31
Create Date: 2026-06-20 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "75cc1d347c32"
down_revision = "74bb1d347c31"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "normalized_financial_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("period_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["period_id"], ["financial_statement_periods.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_normalized_financial_snapshots_company_id"), "normalized_financial_snapshots", ["company_id"], unique=False)
    op.create_index(op.f("ix_normalized_financial_snapshots_period_id"), "normalized_financial_snapshots", ["period_id"], unique=False)

    op.create_table(
        "normalized_financial_metrics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("snapshot_id", sa.Integer(), nullable=False),
        sa.Column("metric_code", sa.String(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(), nullable=True),
        sa.Column("provenance_notes", sa.String(), nullable=True),
        sa.Column("warnings", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["snapshot_id"], ["normalized_financial_snapshots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_normalized_financial_metrics_metric_code"), "normalized_financial_metrics", ["metric_code"], unique=False)
    op.create_index(op.f("ix_normalized_financial_metrics_snapshot_id"), "normalized_financial_metrics", ["snapshot_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_normalized_financial_metrics_snapshot_id"), table_name="normalized_financial_metrics")
    op.drop_index(op.f("ix_normalized_financial_metrics_metric_code"), table_name="normalized_financial_metrics")
    op.drop_table("normalized_financial_metrics")

    op.drop_index(op.f("ix_normalized_financial_snapshots_period_id"), table_name="normalized_financial_snapshots")
    op.drop_index(op.f("ix_normalized_financial_snapshots_company_id"), table_name="normalized_financial_snapshots")
    op.drop_table("normalized_financial_snapshots")
