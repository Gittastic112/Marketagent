from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CountryMarketContext(Base):
    __tablename__ = "country_market_context"
    __table_args__ = (
        UniqueConstraint("market", name="uq_country_market_context_market"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    market: Mapped[str] = mapped_column(String(10), index=True)
    country: Mapped[str] = mapped_column(String(120), index=True)
    currency: Mapped[str] = mapped_column(String(10), index=True)
    risk_free_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_free_rate_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    equity_risk_premium: Mapped[float | None] = mapped_column(Float, nullable=True)
    country_risk_premium: Mapped[float | None] = mapped_column(Float, nullable=True)
    inflation_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    fx_rate_to_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    as_of_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_manual: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
