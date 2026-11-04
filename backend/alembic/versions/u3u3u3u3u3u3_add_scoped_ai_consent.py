"""Record scoped AI permission decisions without granting existing users consent."""

from alembic import op
import sqlalchemy as sa

revision = "u3u3u3u3u3u3"
down_revision = "t2t2t2t2t2t2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_consent_decisions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("provider_name", sa.String(length=50), nullable=False),
        sa.Column("action_key", sa.String(length=60), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=20), nullable=False),
        sa.Column("disclosure_version", sa.String(length=50), nullable=False),
        sa.Column("scope_hash", sa.String(length=64), nullable=False),
        sa.Column("external_data_classes_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "provider_name", "action_key", "revision",
                            name="uq_ai_consent_scope_revision"),
        sa.CheckConstraint("revision >= 1", name="ck_ai_consent_positive_revision"),
        sa.CheckConstraint("state IN ('granted', 'refused', 'revoked')", name="ck_ai_consent_state"),
    )
    op.create_index("ix_ai_consent_decisions_user_id", "ai_consent_decisions", ["user_id"])
    # PostgreSQL adds the nullable field in place; batch mode also supports the
    # isolated SQLite migration regression. No prior output or grant is backfilled.
    with op.batch_alter_table("ai_outputs") as batch:
        batch.add_column(sa.Column("consent_decision_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_ai_outputs_consent_decision", "ai_consent_decisions",
                                 ["consent_decision_id"], ["id"])


def downgrade() -> None:
    with op.batch_alter_table("ai_outputs") as batch:
        batch.drop_constraint("fk_ai_outputs_consent_decision", type_="foreignkey")
        batch.drop_column("consent_decision_id")
    op.drop_index("ix_ai_consent_decisions_user_id", table_name="ai_consent_decisions")
    op.drop_table("ai_consent_decisions")
