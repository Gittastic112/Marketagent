"""Add owned, reproducible extraction evaluation reports.

Revision ID: p7p7p7p7p7p7
Revises: o6o6o6o6o6o6
"""
from alembic import op
import sqlalchemy as sa

revision: str = "p7p7p7p7p7p7"
down_revision: str | None = "o6o6o6o6o6o6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("evaluation_runs", sa.Column("user_id", sa.String(), nullable=True))
    op.add_column("evaluation_runs", sa.Column("report_json", sa.JSON(), nullable=True))
    op.create_foreign_key("fk_evaluation_runs_user_id", "evaluation_runs", "users", ["user_id"], ["id"])
    op.create_index("ix_evaluation_runs_user_id", "evaluation_runs", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_evaluation_runs_user_id", table_name="evaluation_runs")
    op.drop_constraint("fk_evaluation_runs_user_id", "evaluation_runs", type_="foreignkey")
    op.drop_column("evaluation_runs", "report_json")
    op.drop_column("evaluation_runs", "user_id")
