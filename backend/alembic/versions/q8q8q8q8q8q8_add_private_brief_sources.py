"""Add owner-private brief evidence without modifying existing research."""
from alembic import op
import sqlalchemy as sa

revision = "q8q8q8q8q8q8"
down_revision = "p7p7p7p7p7p7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "brief_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("source_kind", sa.String(12), nullable=False),
        sa.Column("source_url", sa.String(1000)),
        sa.Column("as_of_date", sa.Date()),
        sa.Column("identity_hash", sa.String(64), nullable=False),
        sa.Column("source_sha256", sa.String(64), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("pdf_bytes", sa.LargeBinary()),
        sa.Column("extraction_json", sa.JSON(), nullable=False),
        sa.Column("analysis_status", sa.String(24), nullable=False),
        sa.Column("analysis_started_at", sa.DateTime(timezone=True)),
        sa.Column("analysis_json", sa.JSON()),
        sa.Column("ai_output_id", sa.Integer(), sa.ForeignKey("ai_outputs.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "company_id", "identity_hash", name="uq_brief_source_owner_content"),
    )
    op.create_index("ix_brief_sources_user_id", "brief_sources", ["user_id"])
    op.create_index("ix_brief_sources_company_id", "brief_sources", ["company_id"])


def downgrade() -> None:
    op.drop_table("brief_sources")
