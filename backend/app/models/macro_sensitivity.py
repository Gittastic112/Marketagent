from datetime import UTC, date, datetime
from typing import Any, Dict

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)



class SectorMacroSensitivityBenchmark(Base):
    __tablename__ = "sector_macro_sensitivity_benchmarks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_file: Mapped[str] = mapped_column(String(255), index=True)
    market: Mapped[str] = mapped_column(String(10), default="IN", index=True)
    country: Mapped[str] = mapped_column(String(120), default="India", index=True)
    classification_system: Mapped[str] = mapped_column(String(40), default="SIC", index=True)
    currency_context: Mapped[str | None] = mapped_column(String(40), default="INR")
    currency_variable_description: Mapped[str | None] = mapped_column(
        String(500),
        default="Source file currency movement convention not fully verified.",
    )
    sic_code: Mapped[str] = mapped_column(String(20), index=True)
    industry_name: Mapped[str] = mapped_column(String(255), index=True)

    firm_value_duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    firm_value_cyclicality: Mapped[float | None] = mapped_column(Float, nullable=True)
    firm_value_inflation: Mapped[float | None] = mapped_column(Float, nullable=True)
    firm_value_currency: Mapped[float | None] = mapped_column(Float, nullable=True)

    operating_income_duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    operating_income_cyclicality: Mapped[float | None] = mapped_column(Float, nullable=True)
    operating_income_inflation: Mapped[float | None] = mapped_column(Float, nullable=True)
    operating_income_currency: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class CompanyMacroInput(Base):
    __tablename__ = "company_macro_inputs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    period_label: Mapped[str] = mapped_column(String(40), index=True)
    period_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    operating_income: Mapped[float | None] = mapped_column(Float, nullable=True)
    market_cap: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_debt: Mapped[float | None] = mapped_column(Float, nullable=True)
    cash: Mapped[float | None] = mapped_column(Float, nullable=True)
    enterprise_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    source_document_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    company: Mapped["Company"] = relationship("Company", back_populates="macro_inputs")


class CompanyMacroSensitivityResult(Base):
    __tablename__ = "company_macro_sensitivity_results"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    valuation_id: Mapped[int | None] = mapped_column(ForeignKey("valuation_models.id"), nullable=True, index=True)

    method: Mapped[str] = mapped_column(String(40))  # top_down, bottom_up, blended
    dependent_variable: Mapped[str] = mapped_column(String(40))  # firm_value, operating_income
    observation_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    cyclicality: Mapped[float | None] = mapped_column(Float, nullable=True)
    inflation_sensitivity: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency_sensitivity: Mapped[float | None] = mapped_column(Float, nullable=True)

    rate_slope: Mapped[float | None] = mapped_column(Float, nullable=True)
    gdp_slope: Mapped[float | None] = mapped_column(Float, nullable=True)
    inflation_slope: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency_slope: Mapped[float | None] = mapped_column(Float, nullable=True)

    regression_r_squared: Mapped[Dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    confidence_label: Mapped[str | None] = mapped_column(String(40), nullable=True)
    warnings: Mapped[Dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    company: Mapped["Company"] = relationship("Company", back_populates="macro_results")
    valuation: Mapped["ValuationModel"] = relationship("ValuationModel")


class CompanyMacroSegmentExposure(Base):
    __tablename__ = "company_macro_segment_exposures"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    valuation_id: Mapped[int | None] = mapped_column(ForeignKey("valuation_models.id"), nullable=True, index=True)

    segment_name: Mapped[str] = mapped_column(String(255))
    sic_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    benchmark_industry_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    segment_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    segment_revenue: Mapped[float | None] = mapped_column(Float, nullable=True)
    segment_weight: Mapped[float | None] = mapped_column(Float, nullable=True)

    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    cyclicality: Mapped[float | None] = mapped_column(Float, nullable=True)
    inflation_sensitivity: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency_sensitivity: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    company: Mapped["Company"] = relationship("Company", back_populates="macro_segments")
    valuation: Mapped["ValuationModel"] = relationship("ValuationModel")
