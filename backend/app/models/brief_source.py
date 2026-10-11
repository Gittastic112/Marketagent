"""Private, immutable user-supplied evidence, separate from shared filing catalogs."""
from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, ForeignKey, LargeBinary, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BriefSource(Base):
    __tablename__ = "brief_sources"
    __table_args__ = (UniqueConstraint("user_id", "company_id", "identity_hash", name="uq_brief_source_owner_content"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    title: Mapped[str] = mapped_column(String(240))
    source_kind: Mapped[str] = mapped_column(String(12))
    source_url: Mapped[str | None] = mapped_column(String(1000))
    as_of_date: Mapped[date | None] = mapped_column(Date)
    identity_hash: Mapped[str] = mapped_column(String(64))
    source_sha256: Mapped[str] = mapped_column(String(64))
    content_text: Mapped[str] = mapped_column(Text, deferred=True)
    pdf_bytes: Mapped[bytes | None] = mapped_column(LargeBinary, deferred=True)
    extraction_json: Mapped[dict] = mapped_column(JSON)
    analysis_status: Mapped[str] = mapped_column(String(24), default="not_scanned")
    analysis_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    analysis_json: Mapped[dict | None] = mapped_column(JSON)
    ai_output_id: Mapped[int | None] = mapped_column(ForeignKey("ai_outputs.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lifecycle_version: Mapped[int] = mapped_column(default=1, server_default="1")
