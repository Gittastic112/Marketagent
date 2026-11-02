"""Allow unanchored forecast dates without rewriting historical projections."""
from alembic import op
import sqlalchemy as sa

revision = "t2t2t2t2t2t2"
down_revision = "s1s1s1s1s1s1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("dcf_projection_years", "calendar_year",
                    existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    # PostgreSQL rejects this if unknown years exist. Never invent dates, delete
    # projections or rewrite history to force a downgrade.
    op.alter_column("dcf_projection_years", "calendar_year",
                    existing_type=sa.Integer(), nullable=False)
