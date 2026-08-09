"""add damodaran dataset files

Revision ID: 412b1d347c18
Revises: 365a2d347c17
Create Date: 2026-06-17 04:20:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '412b1d347c18'
down_revision = '365a2d347c17'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('damodaran_dataset_files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uploaded_filename', sa.String(length=255), nullable=False),
        sa.Column('dataset_code', sa.String(length=100), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('region', sa.String(length=100), nullable=True),
        sa.Column('date_updated', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source_file_type', sa.String(length=50), nullable=False),
        sa.Column('imported_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_damodaran_dataset_files_dataset_code'), 'damodaran_dataset_files', ['dataset_code'], unique=False)
    op.create_index(op.f('ix_damodaran_dataset_files_id'), 'damodaran_dataset_files', ['id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_damodaran_dataset_files_id'), table_name='damodaran_dataset_files')
    op.drop_index(op.f('ix_damodaran_dataset_files_dataset_code'), table_name='damodaran_dataset_files')
    op.drop_table('damodaran_dataset_files')
