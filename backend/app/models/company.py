from datetime import datetime

from sqlalchemy import JSON, DateTime, String, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    sector: Mapped[str | None] = mapped_column(String(120))
    industry: Mapped[str | None] = mapped_column(String(120))
    exchange: Mapped[str | None] = mapped_column(String(80))
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

    raw_documents = relationship("RawDocument", back_populates="company", lazy="selectin")
    events = relationship("Event", back_populates="company", lazy="selectin")
    alerts = relationship("Alert", back_populates="company", lazy="selectin")
    thesis_notes = relationship("ThesisNote", back_populates="company", lazy="selectin")
    portfolio_holdings = relationship("PortfolioHolding", back_populates="company", lazy="selectin")
    portfolio_transactions = relationship("PortfolioTransaction", back_populates="company", lazy="selectin")
    market_prices = relationship("MarketPrice", back_populates="company", lazy="selectin")
    exposure_tags = relationship("ExposureTag", secondary="company_exposure_tags", back_populates="companies", lazy="selectin")

class ExposureTag(Base):
    __tablename__ = "exposure_tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    companies = relationship("Company", secondary="company_exposure_tags", back_populates="exposure_tags", lazy="selectin")

class CompanyExposureTag(Base):
    __tablename__ = "company_exposure_tags"

    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("exposure_tags.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
