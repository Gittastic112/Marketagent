"""add_research_models

Revision ID: 20260530_1030
Revises: 20260530_1003
Create Date: 2026-05-30 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260530_1030'
down_revision: Union[str, None] = '20260530_1003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('research_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_research_sessions_id'), 'research_sessions', ['id'], unique=False)

    op.create_table('research_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['research_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_research_messages_id'), 'research_messages', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_research_messages_id'), table_name='research_messages')
    op.drop_table('research_messages')
    op.drop_index(op.f('ix_research_sessions_id'), table_name='research_sessions')
    op.drop_table('research_sessions')
