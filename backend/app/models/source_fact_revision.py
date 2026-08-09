from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SourceFactRevision(Base):
    __tablename__ = "source_fact_revisions"
    __table_args__ = (
        UniqueConstraint("financial_candidate_id", name="uq_source_fact_revision_candidate"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    raw_document_id: Mapped[int] = mapped_column(ForeignKey("raw_documents.id", ondelete="CASCADE"), index=True)
    financial_candidate_id: Mapped[int] = mapped_column(
        ForeignKey("financial_extraction_candidates.id", ondelete="CASCADE"),
        index=True,
    )
    fact_key: Mapped[str] = mapped_column(String(100), index=True)
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(100), nullable=True)
    period_type: Mapped[str] = mapped_column(String(40), index=True)
    effective_at: Mapped[date] = mapped_column(Date, index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    revision_number: Mapped[int] = mapped_column(Integer)
    claim_type: Mapped[str] = mapped_column(String(30), default="Fact")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company")
    raw_document = relationship("RawDocument")
    financial_candidate = relationship("FinancialExtractionCandidate")
