"""add ai citation fields

Revision ID: y0y0y0y0y0y0
Revises: x9x9x9x9x9x9
Create Date: 2026-08-09 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'y0y0y0y0y0y0'
down_revision = 'x9x9x9x9x9x9'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add is_blocked to ai_outputs
    op.add_column('ai_outputs', sa.Column('is_blocked', sa.Boolean(), server_default='false', nullable=False))

    # Add ai_output_id to research_messages
    op.add_column('research_messages', sa.Column('ai_output_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_research_messages_ai_output_id', 'research_messages', 'ai_outputs', ['ai_output_id'], ['id'], ondelete='SET NULL')

def downgrade() -> None:
    # Remove ai_output_id from research_messages
    op.drop_constraint('fk_research_messages_ai_output_id', 'research_messages', type_='foreignkey')
    op.drop_column('research_messages', 'ai_output_id')

    # Remove is_blocked from ai_outputs
    op.drop_column('ai_outputs', 'is_blocked')
