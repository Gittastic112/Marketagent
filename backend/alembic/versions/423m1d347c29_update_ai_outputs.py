"""update_ai_outputs

Revision ID: 423m1d347c29
Revises: 422l1d347c28
Create Date: 2026-06-18 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '423m1d347c29'
down_revision: str | Sequence[str] | None = '422l1d347c28'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # make raw_document_id nullable
    op.alter_column('ai_outputs', 'raw_document_id',
               existing_type=sa.INTEGER(),
               nullable=True)

    # add new generic reference columns
    op.add_column('ai_outputs', sa.Column('reference_type', sa.String(length=50), nullable=True))
    op.add_column('ai_outputs', sa.Column('reference_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('ai_outputs', 'reference_id')
    op.drop_column('ai_outputs', 'reference_type')
    op.alter_column('ai_outputs', 'raw_document_id',
               existing_type=sa.INTEGER(),
               nullable=False)
