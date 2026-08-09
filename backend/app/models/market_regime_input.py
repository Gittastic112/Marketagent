from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MarketRegimeInput(Base):
    __tablename__ = "market_regime_inputs"

    id: Mapped[int] = mapped_column(primary_key=True)
    metric_name: Mapped[str] = mapped_column(String(50), index=True) # e.g. "options", "liquidity", "volume", "breadth", "macro"
    value: Mapped[float] = mapped_column(Float)
    as_of_date: Mapped[date] = mapped_column(Date, index=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
