"""add_portfolio_priority_score

Revision ID: 20260530_0718
Revises: 20260529_1015
Create Date: 2026-05-30 07:18:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260530_0718'
down_revision: Union[str, None] = '20260529_1015'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('alerts', sa.Column('portfolio_priority_score', sa.Float(), nullable=False, server_default='0.0'))


def downgrade() -> None:
    op.drop_column('alerts', 'portfolio_priority_score')
