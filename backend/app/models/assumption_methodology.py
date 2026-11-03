from datetime import UTC, datetime
from typing import Any, Dict

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class AssumptionMethodValue(Base):
    __tablename__ = "assumption_method_values"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dataset_file_id: Mapped[int | None] = mapped_column(
        ForeignKey("damodaran_dataset_files.id"),
        index=True,
        nullable=True,
    )
    assumption_key: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    method_key: Mapped[str] = mapped_column(String(100), index=True, nullable=False)

    country: Mapped[str] = mapped_column(String(100), index=True, nullable=True)
    industry: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=True)

    value: Mapped[float] = mapped_column(Float, nullable=False)
    low_value: Mapped[float] = mapped_column(Float, nullable=True)
    base_value: Mapped[float] = mapped_column(Float, nullable=True)
    high_value: Mapped[float] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(50), nullable=False, default="percent")

    source_type: Mapped[str] = mapped_column(String(100), nullable=False) # e.g. "damodaran", "manual", "computed"
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_file: Mapped[str] = mapped_column(String(255), nullable=True)
    source_sheet: Mapped[str] = mapped_column(String(255), nullable=True)
    source_row: Mapped[str] = mapped_column(String(50), nullable=True)
    source_column: Mapped[str] = mapped_column(String(50), nullable=True)

    dataset_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    confidence: Mapped[str] = mapped_column(String(50), nullable=False, default="high")
    is_default_candidate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[str] = mapped_column(String(1000), nullable=True)

    dataset_file = relationship("DamodaranDatasetFile")


class ValuationAssumptionProvenance(Base):
    __tablename__ = "valuation_assumption_provenance"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    valuation_id: Mapped[int] = mapped_column(ForeignKey("valuation_models.id", ondelete="CASCADE"), index=True, nullable=False)

    assumption_key: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    selected_method_key: Mapped[str] = mapped_column(String(100), nullable=False)

    applied_value: Mapped[float] = mapped_column(Float, nullable=False)

    review_status: Mapped[str] = mapped_column(String(50), nullable=False, default="unreviewed") # unreviewed, reviewed, overridden
    source_label: Mapped[str] = mapped_column(String(255), nullable=False) # e.g. "Benchmark-derived", "User override"
    confidence: Mapped[str] = mapped_column(String(50), nullable=False, default="medium")

    notes: Mapped[str] = mapped_column(String(1000), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    valuation = relationship("ValuationModel", back_populates="assumption_provenances")
