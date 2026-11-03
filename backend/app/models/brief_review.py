"""Append-only analyst dispositions, separate from AI approval and financial inputs."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BriefComparisonReview(Base):
    __tablename__ = "brief_comparison_reviews"
    __table_args__ = (UniqueConstraint("user_id", "company_id", "field", "include_mock", "version",
        name="uq_brief_review_scope_version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    field: Mapped[str] = mapped_column(String(64))
    include_mock: Mapped[bool] = mapped_column(Boolean)
    version: Mapped[int] = mapped_column()
    evidence_hash: Mapped[str] = mapped_column(String(64))
    disposition: Mapped[str] = mapped_column(String(32))
    notes: Mapped[str] = mapped_column(Text)
    evidence_json: Mapped[dict] = mapped_column(JSON, deferred=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
