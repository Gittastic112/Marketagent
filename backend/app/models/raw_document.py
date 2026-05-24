from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RawDocument(Base):
    __tablename__ = "raw_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"))
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    document_type: Mapped[str] = mapped_column(String(80), index=True)
    title: Mapped[str] = mapped_column(String(500))
    url: Mapped[str | None] = mapped_column(String(1000))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    raw_text: Mapped[str | None] = mapped_column(Text)
    raw_payload_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    content_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company", back_populates="raw_documents", lazy="selectin")
    source = relationship("Source", back_populates="raw_documents", lazy="selectin")
    events = relationship("Event", back_populates="raw_document", lazy="selectin")
