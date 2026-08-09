from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class CompanySetupWorkflow(Base):
    __tablename__ = "company_setup_workflows"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), unique=True, index=True)
    current_step: Mapped[str] = mapped_column(String(80), default="identity", index=True)
    identity_status: Mapped[str] = mapped_column(String(40), default="needs_review", index=True)
    source_status: Mapped[str] = mapped_column(String(40), default="missing", index=True)
    filing_status: Mapped[str] = mapped_column(String(40), default="missing", index=True)
    financial_extraction_status: Mapped[str] = mapped_column(String(40), default="missing", index=True)
    industry_mapping_status: Mapped[str] = mapped_column(String(40), default="missing", index=True)
    valuation_readiness_status: Mapped[str] = mapped_column(String(40), default="blocked", index=True)
    security_review_status: Mapped[str] = mapped_column(String(40), default="local_only", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    company = relationship("Company")
