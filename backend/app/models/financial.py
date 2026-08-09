from datetime import UTC, date, datetime
from typing import Optional

from sqlalchemy import JSON, ForeignKey, String, Date, Float, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class FinancialStatementPeriod(Base):
    __tablename__ = "financial_statement_periods"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    period_type: Mapped[str] = mapped_column(String, index=True)  # 'annual', 'quarterly'
    year: Mapped[int] = mapped_column(Integer, index=True)
    quarter: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # 1, 2, 3, 4 for quarterly
    report_date: Mapped[date] = mapped_column(Date)
    currency: Mapped[str] = mapped_column(String, default="USD")
    currency_source: Mapped[str] = mapped_column(String(80), default="legacy_unknown")
    currency_confidence: Mapped[str] = mapped_column(String(40), default="unknown")

    created_at: Mapped[datetime] = mapped_column(default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(default=utc_now, onupdate=utc_now)

    company = relationship("Company")
    metrics = relationship("FinancialMetric", back_populates="period", cascade="all, delete-orphan")


class FinancialMetric(Base):
    __tablename__ = "financial_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("financial_statement_periods.id", ondelete="CASCADE"), index=True)
    metric_name: Mapped[str] = mapped_column(String, index=True)
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[Optional[str]] = mapped_column(String, nullable=True) # e.g. 'absolute', 'percentage'

    created_at: Mapped[datetime] = mapped_column(default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(default=utc_now, onupdate=utc_now)

    period = relationship("FinancialStatementPeriod", back_populates="metrics")


class FinancialExtractionCandidate(Base):
    __tablename__ = "financial_extraction_candidates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    raw_document_id: Mapped[int] = mapped_column(ForeignKey("raw_documents.id", ondelete="CASCADE"), index=True)
    metric_code: Mapped[str] = mapped_column(String(80), index=True)
    reported_label: Mapped[str] = mapped_column(String(255))
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    fiscal_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    period_type: Mapped[str] = mapped_column(String(40), default="annual", index=True)
    source_text: Mapped[str] = mapped_column(String)
    source_line_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_section: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_table_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_row_label: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_column_label: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_cell_reference: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    source_locator_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    extraction_warnings: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    extraction_method: Mapped[str] = mapped_column(String(80), default="regex_line_item_v1")
    confidence_label: Mapped[str] = mapped_column(String(40), default="medium")
    review_status: Mapped[str] = mapped_column(String(40), default="needs_review", index=True)
    created_at: Mapped[datetime] = mapped_column(default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(default=utc_now, onupdate=utc_now)

    company = relationship("Company")
    raw_document = relationship("RawDocument")


class NormalizedFinancialSnapshot(Base):
    __tablename__ = "normalized_financial_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("financial_statement_periods.id", ondelete="CASCADE"), index=True)

    created_at: Mapped[datetime] = mapped_column(default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(default=utc_now, onupdate=utc_now)

    company = relationship("Company")
    period = relationship("FinancialStatementPeriod")
    metrics = relationship("NormalizedFinancialMetric", back_populates="snapshot", cascade="all, delete-orphan")


class NormalizedFinancialMetric(Base):
    __tablename__ = "normalized_financial_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("normalized_financial_snapshots.id", ondelete="CASCADE"), index=True)
    metric_code: Mapped[str] = mapped_column(String, index=True)
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    provenance_notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    warnings: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(default=utc_now, onupdate=utc_now)

    snapshot = relationship("NormalizedFinancialSnapshot", back_populates="metrics")

class FinancialReconciliationRecord(Base):
    __tablename__ = "financial_reconciliation_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("financial_statement_periods.id", ondelete="CASCADE"), index=True)

    check_name: Mapped[str] = mapped_column(String(120), index=True)
    is_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    difference: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(default=utc_now, onupdate=utc_now)

    company = relationship("Company")
    period = relationship("FinancialStatementPeriod")
