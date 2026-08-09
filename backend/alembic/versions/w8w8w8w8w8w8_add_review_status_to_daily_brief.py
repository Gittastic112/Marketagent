"""add review_status to daily_briefs

Revision ID: w8w8w8w8w8w8
Revises: v7v7v7v7v7v7
Create Date: 2026-08-08 17:55:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'w8w8w8w8w8w8'
down_revision = 'v7v7v7v7v7v7'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add review_status to daily_briefs table
    op.add_column('daily_briefs', sa.Column('review_status', sa.String(length=50), server_default='new', nullable=False))

def downgrade() -> None:
    op.drop_column('daily_briefs', 'review_status')
