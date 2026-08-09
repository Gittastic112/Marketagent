from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DecisionLog(Base):
    __tablename__ = "decision_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))

    decision_type: Mapped[str] = mapped_column(String(40))  # Buy, Sell, Hold, Trim, Pass
    rationale: Mapped[str] = mapped_column(Text)

    price_at_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    emotional_state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    alternatives_considered: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Stage 14: Research Memory Fields
    current_thesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    valuation: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_readiness: Mapped[str | None] = mapped_column(String(50), nullable=True)
    key_supporting_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_contradictory_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    uncertainties: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_catalysts: Mapped[str | None] = mapped_column(Text, nullable=True)
    what_would_change_the_view: Mapped[str | None] = mapped_column(Text, nullable=True)
    portfolio_context: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    company = relationship("Company", backref="decision_logs", lazy="selectin")
    outcome_review = relationship("OutcomeReview", back_populates="decision_log", uselist=False)

class OutcomeReview(Base):
    __tablename__ = "outcome_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    decision_log_id: Mapped[int] = mapped_column(ForeignKey("decision_logs.id", ondelete="CASCADE"), index=True, unique=True)

    what_happened: Mapped[str] = mapped_column(Text)
    wrong_assumption: Mapped[str | None] = mapped_column(Text, nullable=True)
    information_unavailable_or_misinterpreted: Mapped[bool] = mapped_column(Boolean, default=False)
    valuation_wrong: Mapped[bool] = mapped_column(Boolean, default=False)
    thesis_wrong: Mapped[bool] = mapped_column(Boolean, default=False)
    timing_wrong: Mapped[bool] = mapped_column(Boolean, default=False)
    sizing_wrong: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    decision_log = relationship("DecisionLog", back_populates="outcome_review")
