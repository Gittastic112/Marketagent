from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from app.db.base import Base

class DamodaranRdBenchmark(Base):
    __tablename__ = "industry_rd_benchmarks"

    id = Column(Integer, primary_key=True, index=True)
    dataset_file_id = Column(Integer, ForeignKey("damodaran_dataset_files.id"), nullable=False)
    industry_name = Column(String(255), nullable=False, index=True)
    country = Column(String(100), nullable=True)

    rd_to_sales = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class DamodaranGoodwillBenchmark(Base):
    __tablename__ = "industry_goodwill_benchmarks"

    id = Column(Integer, primary_key=True, index=True)
    dataset_file_id = Column(Integer, ForeignKey("damodaran_dataset_files.id"), nullable=False)
    industry_name = Column(String(255), nullable=False, index=True)
    country = Column(String(100), nullable=True)

    goodwill_to_assets = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CompanyRdHistory(Base):
    __tablename__ = "company_rd_history"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)

    year = Column(Integer, nullable=False)
    rd_expense = Column(Float, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ValuationAccountingAdjustment(Base):
    __tablename__ = "valuation_accounting_adjustments"

    id = Column(Integer, primary_key=True, index=True)
    valuation_run_id = Column(Integer, ForeignKey("valuation_models.id"), nullable=False)

    adjustment_type = Column(String(50), nullable=False) # e.g. "rd_capitalization", "goodwill_impairment"
    original_value = Column(Float, nullable=True)
    adjusted_value = Column(Float, nullable=True)
    details_json = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
