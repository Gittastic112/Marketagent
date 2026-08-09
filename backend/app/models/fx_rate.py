from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Date, DateTime, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FxRateObservation(Base):
    """A dated quote-currency amount for one unit of the base currency."""

    __tablename__ = "fx_rate_observations"
    __table_args__ = (
        UniqueConstraint(
            "base_currency",
            "quote_currency",
            "as_of_date",
            "provider_name",
            name="uq_fx_rate_observation_source_date",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    base_currency: Mapped[str] = mapped_column(String(10), index=True)
    quote_currency: Mapped[str] = mapped_column(String(10), index=True)
    rate: Mapped[Decimal] = mapped_column(Numeric(24, 10))
    as_of_date: Mapped[date] = mapped_column(Date, index=True)
    provider_name: Mapped[str] = mapped_column(String(80), default="manual", index=True)
    provider_symbol: Mapped[str | None] = mapped_column(String(80), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    source_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
