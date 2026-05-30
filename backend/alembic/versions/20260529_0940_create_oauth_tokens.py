"""create oauth tokens

Revision ID: 0014_create_oauth_tokens
Revises: 20260528_2035_create_ai  # Wait, I should find the latest revision ID.
Create Date: 2026-05-29 09:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260529_0940'
down_revision = '20260528_2035'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('oauth_tokens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('provider_name', sa.String(length=120), nullable=False),
    sa.Column('encrypted_access_token', sa.String(length=2000), nullable=False),
    sa.Column('encrypted_refresh_token', sa.String(length=2000), nullable=True),
    sa.Column('scopes', sa.String(length=500), nullable=True),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_oauth_tokens_provider_name'), 'oauth_tokens', ['provider_name'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_oauth_tokens_provider_name'), table_name='oauth_tokens')
    op.drop_table('oauth_tokens')
