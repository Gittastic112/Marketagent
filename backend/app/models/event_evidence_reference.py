from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EventEvidenceReference(Base):
    __tablename__ = "event_evidence_references"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        index=True,
    )
    raw_document_id: Mapped[int] = mapped_column(
        ForeignKey("raw_documents.id", ondelete="CASCADE"),
        index=True,
    )
    created_by_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    locator_type: Mapped[str] = mapped_column(String(30), index=True)
    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_section: Mapped[str | None] = mapped_column(String(500), nullable=True)
    start_char: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_char: Mapped[int | None] = mapped_column(Integer, nullable=True)
    quote: Mapped[str | None] = mapped_column(Text, nullable=True)
    bounding_box_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    source_metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    confidence_label: Mapped[str] = mapped_column(String(20), default="high")
    origin: Mapped[str] = mapped_column(String(30), default="manual_review")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    event = relationship("Event", back_populates="evidence_references")
    raw_document = relationship("RawDocument", lazy="selectin")
