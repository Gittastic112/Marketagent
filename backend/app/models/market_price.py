from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MarketPrice(Base):
    __tablename__ = "market_prices"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), index=True)
    ticker: Mapped[str] = mapped_column(String(20), index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    as_of_date: Mapped[date] = mapped_column(Date, index=True)
    provider_name: Mapped[str] = mapped_column(String(50), default="manual", index=True)
    provider_symbol: Mapped[str | None] = mapped_column(String(50))
    market: Mapped[str | None] = mapped_column(String(20))
    exchange: Mapped[str | None] = mapped_column(String(30))
    source_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    price_type: Mapped[str] = mapped_column(String(30), default="manual")
    delay_minutes: Mapped[int | None] = mapped_column()
    adjustment_state: Mapped[str] = mapped_column(String(30), default="not_applicable")
    warnings_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    company = relationship("Company", back_populates="market_prices", lazy="selectin")

    @property
    def warnings(self) -> list[str]:
        return self.warnings_json or []


class CompanyMarketData(Base):
    __tablename__ = "company_market_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), unique=True, index=True)
    current_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    currency: Mapped[str | None] = mapped_column(String(10), default="USD")
    change_percent: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    volume: Mapped[int | None] = mapped_column()
    market_cap: Mapped[Decimal | None] = mapped_column(Numeric(25, 2))
    pe_ratio: Mapped[Decimal | None] = mapped_column(Numeric(10, 4))
    fifty_two_week_high: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    fifty_two_week_low: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    provider_name: Mapped[str] = mapped_column(String(50), default="legacy_unknown")
    provider_symbol: Mapped[str | None] = mapped_column(String(50))
    source_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    price_type: Mapped[str] = mapped_column(String(30), default="unknown")
    delay_minutes: Mapped[int | None] = mapped_column()
    adjustment_state: Mapped[str] = mapped_column(String(30), default="unknown")
    warnings_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    company = relationship("Company", back_populates="market_data", lazy="selectin")

    @property
    def warnings(self) -> list[str]:
        return self.warnings_json or []
