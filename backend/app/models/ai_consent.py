"""Append-only decisions for explicitly scoped external AI transfers."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AiConsentDecision(Base):
    __tablename__ = "ai_consent_decisions"
    __table_args__ = (
        UniqueConstraint("user_id", "provider_name", "action_key", "revision",
                         name="uq_ai_consent_scope_revision"),
        CheckConstraint("revision >= 1", name="ck_ai_consent_positive_revision"),
        CheckConstraint("state IN ('granted', 'refused', 'revoked')",
                        name="ck_ai_consent_state"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    provider_name: Mapped[str] = mapped_column(String(50), nullable=False)
    action_key: Mapped[str] = mapped_column(String(60), nullable=False)
    revision: Mapped[int] = mapped_column(nullable=False)
    state: Mapped[str] = mapped_column(String(20), nullable=False)
    disclosure_version: Mapped[str] = mapped_column(String(50), nullable=False)
    scope_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    external_data_classes_json: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
