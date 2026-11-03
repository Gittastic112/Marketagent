from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MarketRegimeInput(Base):
    __tablename__ = "market_regime_inputs"
    __table_args__ = (
        UniqueConstraint(
            "metric_name",
            "input_type",
            "source_record_type",
            "source_record_id",
            name="uq_market_regime_provider_source_record",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    metric_name: Mapped[str] = mapped_column(String(50), index=True) # e.g. "options", "liquidity", "volume", "breadth", "macro"
    value: Mapped[float] = mapped_column(Float)
    as_of_date: Mapped[date] = mapped_column(Date, index=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_name: Mapped[str] = mapped_column(String(200))
    input_type: Mapped[str] = mapped_column(String(30), default="manual")
    methodology: Mapped[str] = mapped_column(String(1000))
    source_record_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    source_record_id: Mapped[int | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
