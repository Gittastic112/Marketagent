"""Add PostgreSQL full-text evidence indexes.

Revision ID: g3g3g3g3g3g3
Revises: f2f2f2f2f2f2
Create Date: 2026-07-31
"""

from alembic import op


revision = "g3g3g3g3g3g3"
down_revision = "f2f2f2f2f2f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX ix_raw_documents_search_vector ON raw_documents USING gin "
        "(to_tsvector('english', coalesce(title, '') || ' ' || coalesce(raw_text, '')))"
    )
    op.execute(
        "CREATE INDEX ix_events_search_vector ON events USING gin "
        "(to_tsvector('english', coalesce(title, '') || ' ' || coalesce(description, '')))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_events_search_vector")
    op.execute("DROP INDEX IF EXISTS ix_raw_documents_search_vector")
