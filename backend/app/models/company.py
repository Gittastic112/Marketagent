from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (
        UniqueConstraint("market", "primary_exchange", "local_symbol", name="uq_companies_market_exchange_symbol"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(20), index=True)
    name: Mapped[str] = mapped_column(String(255))
    sector: Mapped[str | None] = mapped_column(String(120))
    industry: Mapped[str | None] = mapped_column(String(120))
    damodaran_industry: Mapped[str | None] = mapped_column(String(120))
    exchange: Mapped[str | None] = mapped_column(String(80))
    market: Mapped[str] = mapped_column(String(10), default="US", index=True)
    primary_exchange: Mapped[str | None] = mapped_column(String(20), index=True)
    local_symbol: Mapped[str | None] = mapped_column(String(40), index=True)
    isin: Mapped[str | None] = mapped_column(String(20), index=True)
    figi: Mapped[str | None] = mapped_column(String(32), index=True)
    regulatory_id: Mapped[str | None] = mapped_column(String(40), index=True)
    regulatory_id_type: Mapped[str | None] = mapped_column(String(40))
    cik: Mapped[str | None] = mapped_column(String(20), unique=True)
    aliases_json: Mapped[list[str] | None] = mapped_column(JSON)
    country: Mapped[str | None] = mapped_column(String(120))
    region: Mapped[str | None] = mapped_column(String(120))
    currency: Mapped[str | None] = mapped_column(String(10))
    asset_type: Mapped[str | None] = mapped_column(String(80))
    security_type: Mapped[str | None] = mapped_column(String(80))
    market_cap_category: Mapped[str | None] = mapped_column(String(80))
    is_etf: Mapped[bool] = mapped_column(default=False)
    etf_provider: Mapped[str | None] = mapped_column(String(120))
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # A company identity must not recursively load its entire research/portfolio
    # history. Workflows opt into eager loading the relationships they actually use.
    raw_documents = relationship("RawDocument", back_populates="company", lazy="select")
    events = relationship("Event", back_populates="company", lazy="select")
    alerts = relationship("Alert", back_populates="company", lazy="select")
    thesis_notes = relationship("ThesisNote", back_populates="company", lazy="select")
    portfolio_holdings = relationship("PortfolioHolding", back_populates="company", lazy="select")
    portfolio_transactions = relationship("PortfolioTransaction", back_populates="company", lazy="select")
    market_prices = relationship("MarketPrice", back_populates="company", lazy="select")
    market_data = relationship("CompanyMarketData", back_populates="company", lazy="select", uselist=False)
    exposure_tags = relationship("ExposureTag", secondary="company_exposure_tags", back_populates="companies", lazy="selectin")

    macro_inputs = relationship("CompanyMacroInput", back_populates="company", lazy="select")
    macro_results = relationship("CompanyMacroSensitivityResult", back_populates="company", lazy="select")
    macro_segments = relationship("CompanyMacroSegmentExposure", back_populates="company", lazy="select")

class ExposureTag(Base):
    __tablename__ = "exposure_tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    companies = relationship("Company", secondary="company_exposure_tags", back_populates="exposure_tags", lazy="select")

class CompanyExposureTag(Base):
    __tablename__ = "company_exposure_tags"

    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("exposure_tags.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
