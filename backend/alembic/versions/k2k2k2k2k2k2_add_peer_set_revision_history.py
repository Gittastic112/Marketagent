"""add peer valuation set revision history

Revision ID: k2k2k2k2k2k2
Revises: j1j1j1j1j1j1
Create Date: 2026-08-26
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "k2k2k2k2k2k2"
down_revision: str | None = "j1j1j1j1j1j1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "peer_valuation_sets",
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
    )
    revisions = op.create_table(
        "peer_valuation_set_revisions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("peer_set_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=30), nullable=False),
        sa.Column("changed_fields_json", sa.JSON(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("review_status", sa.String(length=20), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by_user_id", sa.String(), nullable=True),
        sa.Column("aggregation_method", sa.String(length=20), nullable=False),
        sa.Column("members_json", sa.JSON(), nullable=False),
        sa.Column("aggregate_metrics_json", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["peer_set_id"],
            ["peer_valuation_sets.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["reviewed_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "peer_set_id",
            "version",
            name="uq_peer_valuation_set_revisions_set_version",
        ),
    )
    op.create_index(
        "ix_peer_valuation_set_revisions_peer_set_id",
        "peer_valuation_set_revisions",
        ["peer_set_id"],
    )
    op.create_index(
        "ix_peer_valuation_set_revisions_user_id",
        "peer_valuation_set_revisions",
        ["user_id"],
    )
    op.create_index(
        "ix_peer_valuation_set_revisions_action",
        "peer_valuation_set_revisions",
        ["action"],
    )

    connection = op.get_bind()
    existing_sets = connection.execute(
        sa.text(
            """
            SELECT id, user_id, name, notes, is_active, review_status,
                   reviewed_at, reviewed_by_user_id, aggregation_method,
                   peer_identifiers_json, aggregate_metrics_json, created_at
            FROM peer_valuation_sets
            """
        )
    ).mappings()
    snapshots = [
            {
                "peer_set_id": row["id"],
                "user_id": row["user_id"],
                "version": 1,
                "action": "migration_snapshot",
                "changed_fields_json": ["migrationSnapshot"],
                "name": row["name"],
                "notes": row["notes"],
                "is_active": row["is_active"],
                "review_status": row["review_status"],
                "reviewed_at": row["reviewed_at"],
                "reviewed_by_user_id": row["reviewed_by_user_id"],
                "aggregation_method": row["aggregation_method"],
                "members_json": row["peer_identifiers_json"] or [],
                "aggregate_metrics_json": row["aggregate_metrics_json"] or {},
                "created_at": row["created_at"],
            }
            for row in existing_sets
        ]
    if snapshots:
        op.bulk_insert(revisions, snapshots)


def downgrade() -> None:
    op.drop_table("peer_valuation_set_revisions")
    op.drop_column("peer_valuation_sets", "version")
