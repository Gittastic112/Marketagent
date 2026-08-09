from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MarketSourceCapability(Base):
    __tablename__ = "market_source_capabilities"
    __table_args__ = (
        UniqueConstraint(
            "market",
            "source_type",
            "provider_name",
            "capability",
            name="uq_market_source_capability",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    market: Mapped[str] = mapped_column(String(10), index=True)
    source_type: Mapped[str] = mapped_column(String(80), index=True)
    provider_name: Mapped[str] = mapped_column(String(120), index=True)
    capability: Mapped[str] = mapped_column(String(120), index=True)
    status: Mapped[str] = mapped_column(String(40), index=True)
    requires_api_key: Mapped[bool] = mapped_column(Boolean, default=False)
    freshness_expected_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
