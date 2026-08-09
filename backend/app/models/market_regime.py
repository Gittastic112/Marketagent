from datetime import date, datetime
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Float, String, Text, func, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MarketRegimeScore(Base):
    __tablename__ = "market_regime_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    score_date: Mapped[date] = mapped_column(Date, index=True)

    overall_score: Mapped[float] = mapped_column(Float)

    # Module Scores
    options_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    liquidity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    volume_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    breadth_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    macro_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Context
    confidence: Mapped[str] = mapped_column(String(50), default="low")
    warnings: Mapped[list[str]] = mapped_column(JSON, default=list)
    calculation_status: Mapped[str] = mapped_column(String(30), default="blocked")
    formula: Mapped[str] = mapped_column(Text, default="")
    blockers: Mapped[list[str]] = mapped_column(JSON, default=list)
    input_sources: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)

    # Prototype Mode Tracking
    mode: Mapped[str] = mapped_column(String(50), default="Prototype")
    live_modules: Mapped[list[str]] = mapped_column(JSON, default=list)
    manual_modules: Mapped[list[str]] = mapped_column(JSON, default=list)
    simulated_modules: Mapped[list[str]] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
