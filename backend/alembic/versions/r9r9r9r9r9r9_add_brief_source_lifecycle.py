"""Add reversible organization without rewriting source evidence."""
from alembic import op
import sqlalchemy as sa

revision = "r9r9r9r9r9r9"
down_revision = "q8q8q8q8q8q8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("brief_sources", sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("brief_sources", sa.Column("lifecycle_version", sa.Integer(), nullable=False, server_default="1"))


def downgrade() -> None:
    op.drop_column("brief_sources", "lifecycle_version")
    op.drop_column("brief_sources", "archived_at")
