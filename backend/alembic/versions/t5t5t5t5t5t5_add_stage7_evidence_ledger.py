"""add stage7 evidence ledger

Revision ID: t5t5t5t5t5t5
Revises: s4s4s4s4s4s4
Create Date: 2026-08-08 17:13:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 't5t5t5t5t5t5'
down_revision: Union[str, None] = 's4s4s4s4s4s4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to event_thesis_impacts
    op.add_column('event_thesis_impacts', sa.Column('claim', sa.Text(), nullable=True))
    op.add_column('event_thesis_impacts', sa.Column('importance', sa.String(length=40), nullable=False, server_default='medium'))
    op.add_column('event_thesis_impacts', sa.Column('confidence', sa.String(length=40), nullable=False, server_default='medium'))
    op.add_column('event_thesis_impacts', sa.Column('review_status', sa.String(length=40), nullable=False, server_default='unreviewed'))


def downgrade() -> None:
    op.drop_column('event_thesis_impacts', 'review_status')
    op.drop_column('event_thesis_impacts', 'confidence')
    op.drop_column('event_thesis_impacts', 'importance')
    op.drop_column('event_thesis_impacts', 'claim')
