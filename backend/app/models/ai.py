from datetime import datetime

from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AiOutput(Base):
    __tablename__ = "ai_outputs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    raw_document_id: Mapped[int | None] = mapped_column(ForeignKey("raw_documents.id", ondelete="CASCADE"), index=True, nullable=True)

    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True) # e.g. "valuation_run", "dcf_assumption_set"
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    model_name: Mapped[str] = mapped_column(String(100))
    provider_name: Mapped[str] = mapped_column(String(50), default="legacy_unknown")
    is_mock: Mapped[bool] = mapped_column(Boolean, default=False)
    prompt_version: Mapped[str] = mapped_column(String(50))
    input_hash: Mapped[str] = mapped_column(String(128))

    source_ids_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    source_scope: Mapped[str] = mapped_column(String(100), default="unspecified")
    citations_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    citation_validation_status: Mapped[str] = mapped_column(String(30), default="not_evaluated")
    evaluation_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    privacy_disclosure_version: Mapped[str] = mapped_column(String(50), default="v1")
    external_data_classes_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    transmission_scope: Mapped[str] = mapped_column(String(50), default="external_provider")
    execution_status: Mapped[str] = mapped_column(String(30), default="success")
    failure_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)

    output_text: Mapped[str] = mapped_column(Text)
    limitations: Mapped[str | None] = mapped_column(Text)
    confidence_label: Mapped[str] = mapped_column(String(50))
    human_review_status: Mapped[str] = mapped_column(String(50), default="pending")
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewer_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    raw_document = relationship("RawDocument", backref="ai_outputs", lazy="selectin")
