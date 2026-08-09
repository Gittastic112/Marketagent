from datetime import datetime, UTC
from typing import Any

from sqlalchemy import Float, ForeignKey, Integer, String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EntityScore(Base):
    __tablename__ = "entity_scores"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True, unique=True)

    # 0 to 100 scale scores
    fundamental_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    valuation_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    narrative_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sentiment_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    momentum_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    overall_confidence_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Optional detailed JSON for provenance/breakdown of the score
    score_breakdown_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    company = relationship("Company")
