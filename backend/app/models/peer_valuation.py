from datetime import datetime, UTC
from typing import Any

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PeerValuationSet(Base):
    __tablename__ = "peer_valuation_sets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    name: Mapped[str] = mapped_column(String(120))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Store list of peer company IDs or tickers as a JSON array
    peer_identifiers_json: Mapped[list[str]] = mapped_column(JSON, default=list)

    # Pre-calculated aggregates for the peer set (e.g. median EV/EBITDA, mean P/E)
    aggregate_metrics_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    notes: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    company = relationship("Company")
