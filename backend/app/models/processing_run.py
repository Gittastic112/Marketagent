from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.request_context import get_request_id
from app.db.base import Base


class ProcessingRun(Base):
    __tablename__ = "processing_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[str | None] = mapped_column(
        String(36),
        default=get_request_id,
        index=True,
        nullable=True,
    )
    run_type: Mapped[str] = mapped_column(String(80), index=True)
    source_type: Mapped[str | None] = mapped_column(String(80), index=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"))
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(40), index=True)
    fetched_count: Mapped[int] = mapped_column(default=0)
    created_count: Mapped[int] = mapped_column(default=0)
    skipped_duplicate_count: Mapped[int] = mapped_column(default=0)
    error_count: Mapped[int] = mapped_column(default=0)
    error_details_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source = relationship("Source", lazy="selectin")
    company = relationship("Company", lazy="selectin")
