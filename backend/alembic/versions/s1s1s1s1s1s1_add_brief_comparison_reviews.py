"""Add private append-only comparison review receipts. No evidence rewrite."""
from alembic import op
import sqlalchemy as sa

revision = "s1s1s1s1s1s1"
down_revision = "r9r9r9r9r9r9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("brief_comparison_reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("field", sa.String(64), nullable=False),
        sa.Column("include_mock", sa.Boolean(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("evidence_hash", sa.String(64), nullable=False),
        sa.Column("disposition", sa.String(32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("evidence_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "company_id", "field", "include_mock", "version", name="uq_brief_review_scope_version"))
    op.create_index("ix_brief_comparison_reviews_user_id", "brief_comparison_reviews", ["user_id"])
    op.create_index("ix_brief_comparison_reviews_company_id", "brief_comparison_reviews", ["company_id"])


def downgrade() -> None:
    op.drop_table("brief_comparison_reviews")
