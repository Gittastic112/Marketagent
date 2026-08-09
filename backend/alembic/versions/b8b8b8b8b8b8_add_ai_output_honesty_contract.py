"""add AI output honesty contract

Revision ID: b8b8b8b8b8b8
Revises: a7a7a7a7a7a7
Create Date: 2026-07-26 11:15:00.000000
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "b8b8b8b8b8b8"
down_revision: str | Sequence[str] | None = "a7a7a7a7a7a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("ai_outputs", sa.Column("user_id", sa.String(length=255), nullable=True))
    op.add_column("ai_outputs", sa.Column("provider_name", sa.String(length=50), nullable=True))
    op.add_column("ai_outputs", sa.Column("is_mock", sa.Boolean(), nullable=True))
    op.add_column("ai_outputs", sa.Column("source_ids_json", sa.JSON(), nullable=True))
    op.add_column("ai_outputs", sa.Column("source_scope", sa.String(length=100), nullable=True))
    op.add_column("ai_outputs", sa.Column("privacy_disclosure_version", sa.String(length=50), nullable=True))
    op.add_column("ai_outputs", sa.Column("external_data_classes_json", sa.JSON(), nullable=True))
    op.add_column("ai_outputs", sa.Column("transmission_scope", sa.String(length=50), nullable=True))
    op.add_column("ai_outputs", sa.Column("execution_status", sa.String(length=30), nullable=True))
    op.add_column("ai_outputs", sa.Column("failure_code", sa.String(length=100), nullable=True))
    op.add_column("ai_outputs", sa.Column("reviewer_id", sa.String(length=255), nullable=True))
    op.add_column("ai_outputs", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))

    op.execute(
        """
        UPDATE ai_outputs
        SET user_id = 'admin_user_id_fallback',
            provider_name = 'legacy_unknown',
            is_mock = true,
            source_ids_json = '[]',
            source_scope = 'legacy_unspecified',
            privacy_disclosure_version = 'legacy',
            external_data_classes_json = '[]',
            transmission_scope = 'unknown',
            execution_status = 'success'
        """
    )

    for column in (
        "user_id",
        "provider_name",
        "is_mock",
        "source_ids_json",
        "source_scope",
        "privacy_disclosure_version",
        "external_data_classes_json",
        "transmission_scope",
        "execution_status",
    ):
        op.alter_column("ai_outputs", column, nullable=False)

    op.create_index(op.f("ix_ai_outputs_user_id"), "ai_outputs", ["user_id"], unique=False)
    op.create_index(
        "ix_ai_outputs_user_reference",
        "ai_outputs",
        ["user_id", "reference_type", "reference_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_ai_outputs_user_id_users",
        "ai_outputs",
        "users",
        ["user_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_ai_outputs_reviewer_id_users",
        "ai_outputs",
        "users",
        ["reviewer_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_ai_outputs_reviewer_id_users", "ai_outputs", type_="foreignkey")
    op.drop_constraint("fk_ai_outputs_user_id_users", "ai_outputs", type_="foreignkey")
    op.drop_index("ix_ai_outputs_user_reference", table_name="ai_outputs")
    op.drop_index(op.f("ix_ai_outputs_user_id"), table_name="ai_outputs")
    for column in (
        "reviewed_at",
        "reviewer_id",
        "failure_code",
        "execution_status",
        "transmission_scope",
        "external_data_classes_json",
        "privacy_disclosure_version",
        "source_scope",
        "source_ids_json",
        "is_mock",
        "provider_name",
        "user_id",
    ):
        op.drop_column("ai_outputs", column)
