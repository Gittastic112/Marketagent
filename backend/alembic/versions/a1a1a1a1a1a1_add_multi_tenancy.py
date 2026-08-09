"""add_multi_tenancy

Revision ID: a1a1a1a1a1a1
Revises: 8550649236ca
Create Date: 2026-06-21 07:18:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'a1a1a1a1a1a1'
down_revision: str | Sequence[str] | None = '8550649236ca'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create users table
    op.create_table('users',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. Insert a default admin user to avoid dropping data
    op.execute(
        "INSERT INTO users (id, email, name) VALUES ('admin_user_id_fallback', 'admin@example.com', 'Admin Fallback')"
    )

    # 3. Add user_id column as nullable initially
    tables = [
        "portfolios",
        "valuation_models",
        "alerts",
        "thesis_notes",
        "daily_briefs",
        "decision_logs",
        "research_sessions",
        "company_macro_inputs",
    ]

    for table in tables:
        op.add_column(table, sa.Column('user_id', sa.String(length=255), nullable=True))

        # 4. Update existing records
        op.execute(f"UPDATE {table} SET user_id = 'admin_user_id_fallback' WHERE user_id IS NULL")

        # 5. Make column non-nullable
        op.alter_column(table, 'user_id', nullable=False)

        # 6. Add foreign key and index
        op.create_index(op.f(f'ix_{table}_user_id'), table, ['user_id'], unique=False)
        op.create_foreign_key(f"fk_{table}_user_id_users", table, "users", ["user_id"], ["id"])


def downgrade() -> None:
    tables = [
        "portfolios",
        "valuation_models",
        "alerts",
        "thesis_notes",
        "daily_briefs",
        "decision_logs",
        "research_sessions",
        "company_macro_inputs",
    ]

    for table in reversed(tables):
        op.drop_constraint(f"fk_{table}_user_id_users", table, type_='foreignkey')
        op.drop_index(op.f(f'ix_{table}_user_id'), table_name=table)
        op.drop_column(table, 'user_id')

    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
