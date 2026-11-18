"""Store private thesis annotations with immutable price snapshots."""
import sqlalchemy as sa
from alembic import op

revision = "w5w5w5w5w5w5"
down_revision = "v4v4v4v4v4v4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "thesis_price_pins",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("thesis_note_id", sa.Integer(), sa.ForeignKey("thesis_notes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("request_id", sa.String(36), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("anchor", sa.JSON(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("thesis_note_id", "request_id", name="uq_thesis_price_pin_request"),
    )
    for column in ("company_id", "thesis_note_id", "fingerprint"):
        op.create_index(f"ix_thesis_price_pins_{column}", "thesis_price_pins", [column])


def downgrade() -> None:
    op.drop_table("thesis_price_pins")
