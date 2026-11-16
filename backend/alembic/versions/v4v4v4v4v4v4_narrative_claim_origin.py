"""Retain exact new narrative origins without rewriting existing claims."""
from alembic import op
import sqlalchemy as sa

revision = "v4v4v4v4v4v4"
down_revision = "u3u3u3u3u3u3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("narrative_claims") as batch:
        batch.add_column(sa.Column("origin", sa.String(30), nullable=True))
        batch.add_column(sa.Column("ai_output_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_narrative_claim_ai_output", "ai_outputs", ["ai_output_id"], ["id"])
        batch.create_index("ix_narrative_claims_ai_output_id", ["ai_output_id"])


def downgrade() -> None:
    with op.batch_alter_table("narrative_claims") as batch:
        batch.drop_index("ix_narrative_claims_ai_output_id")
        batch.drop_constraint("fk_narrative_claim_ai_output", type_="foreignkey")
        batch.drop_column("ai_output_id")
        batch.drop_column("origin")
