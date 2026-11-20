"""Add optional original dataset publication evidence and typed thesis decisions."""
import sqlalchemy as sa
from alembic import op

revision = "x6x6x6x6x6x6"
down_revision = "w5w5w5w5w5w5"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("damodaran_dataset_files", sa.Column("publication_date", sa.Date(), nullable=True))
    op.add_column("damodaran_dataset_files", sa.Column("publication_source", sa.String(1000), nullable=True))
    op.add_column("thesis_changes", sa.Column("request_id", sa.String(36), nullable=True))
    op.add_column("thesis_changes", sa.Column("price_review", sa.JSON(), nullable=True))
    op.create_index("uq_thesis_change_request", "thesis_changes", ["thesis_note_id", "request_id"], unique=True)


def downgrade():
    op.drop_index("uq_thesis_change_request", table_name="thesis_changes")
    op.drop_column("thesis_changes", "price_review")
    op.drop_column("thesis_changes", "request_id")
    op.drop_column("damodaran_dataset_files", "publication_source")
    op.drop_column("damodaran_dataset_files", "publication_date")
