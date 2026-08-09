from datetime import datetime, UTC
from typing import Any

from sqlalchemy import Boolean, ForeignKey, Integer, String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DecisionReadiness(Base):
    __tablename__ = "decision_readiness"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True, unique=True)

    financial_ready: Mapped[bool] = mapped_column(Boolean, default=False)
    valuation_ready: Mapped[bool] = mapped_column(Boolean, default=False)
    thesis_ready: Mapped[bool] = mapped_column(Boolean, default=False)
    evidence_ready: Mapped[bool] = mapped_column(Boolean, default=False)
    portfolio_ready: Mapped[bool] = mapped_column(Boolean, default=False)
    catalyst_ready: Mapped[bool] = mapped_column(Boolean, default=False)

    # overall status, e.g., "Ready", "Partial", "Blocked"
    overall_status: Mapped[str] = mapped_column(String(50), default="Blocked")

    blocking_issues_json: Mapped[list[str]] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    company = relationship("Company")
