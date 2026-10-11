"""add daily brief schedules

Revision ID: ee6ee6ee6ee6
Revises: dd5dd5dd5dd5
Create Date: 2026-08-23 12:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "ee6ee6ee6ee6"
down_revision: str | None = "dd5dd5dd5dd5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "daily_brief_schedules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(length=255), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("timezone", sa.String(length=64), server_default="UTC", nullable=False),
        sa.Column("local_time", sa.Time(), server_default="07:00:00", nullable=False),
        sa.Column("days_of_week", sa.JSON(), nullable=False),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_succeeded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status", sa.String(length=40), server_default="disabled", nullable=False),
        sa.Column("last_processing_run_id", sa.Integer(), nullable=True),
        sa.Column("last_brief_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["last_brief_id"], ["daily_briefs.id"]),
        sa.ForeignKeyConstraint(["last_processing_run_id"], ["processing_runs.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_daily_brief_schedules_user_id", "daily_brief_schedules", ["user_id"])
    op.create_index("ix_daily_brief_schedules_next_run_at", "daily_brief_schedules", ["next_run_at"])
    op.create_index("ix_daily_brief_schedules_lease_expires_at", "daily_brief_schedules", ["lease_expires_at"])


def downgrade() -> None:
    op.drop_index("ix_daily_brief_schedules_lease_expires_at", table_name="daily_brief_schedules")
    op.drop_index("ix_daily_brief_schedules_next_run_at", table_name="daily_brief_schedules")
    op.drop_index("ix_daily_brief_schedules_user_id", table_name="daily_brief_schedules")
    op.drop_table("daily_brief_schedules")
