from datetime import date, datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Date, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FinancialStatementPeriod(Base):
    __tablename__ = "financial_statement_periods"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    period_type: Mapped[str] = mapped_column(String, index=True)  # 'annual', 'quarterly'
    year: Mapped[int] = mapped_column(Integer, index=True)
    quarter: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # 1, 2, 3, 4 for quarterly
    report_date: Mapped[date] = mapped_column(Date)
    currency: Mapped[str] = mapped_column(String, default="USD")

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company")
    metrics = relationship("FinancialMetric", back_populates="period", cascade="all, delete-orphan")


class FinancialMetric(Base):
    __tablename__ = "financial_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("financial_statement_periods.id", ondelete="CASCADE"), index=True)
    metric_name: Mapped[str] = mapped_column(String, index=True)
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[Optional[str]] = mapped_column(String, nullable=True) # e.g. 'absolute', 'percentage'

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    period = relationship("FinancialStatementPeriod", back_populates="metrics")
