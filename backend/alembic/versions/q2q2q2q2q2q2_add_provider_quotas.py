"""add provider quotas

Revision ID: q2q2q2q2q2q2
Revises: p1p1p1p1p1p1
Create Date: 2026-08-08 15:26:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'q2q2q2q2q2q2'
down_revision = 'p1p1p1p1p1p1'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'provider_quotas',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('provider_name', sa.String(length=120), nullable=False),
        sa.Column('quota_window', sa.String(length=40), nullable=False),
        sa.Column('estimated_quota', sa.Integer(), nullable=False),
        sa.Column('calls_used', sa.Integer(), nullable=False),
        sa.Column('last_successful_call', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_safe_refresh', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider_name', 'quota_window', name='uq_provider_quota_window')
    )
    op.create_index(op.f('ix_provider_quotas_provider_name'), 'provider_quotas', ['provider_name'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_provider_quotas_provider_name'), table_name='provider_quotas')
    op.drop_table('provider_quotas')
