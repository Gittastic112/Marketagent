from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int | None] = mapped_column(ForeignKey("events.id"))
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"))
    alert_type: Mapped[str] = mapped_column(String(100), index=True)
    severity: Mapped[str] = mapped_column(String(40), default="low")
    title: Mapped[str] = mapped_column(String(500))
    summary: Mapped[str | None] = mapped_column(Text)
    why_it_matters: Mapped[str | None] = mapped_column(Text)
    what_changed: Mapped[str | None] = mapped_column(Text)
    evidence: Mapped[str | None] = mapped_column(Text)
    confidence_bucket: Mapped[str] = mapped_column(String(20), default="low")
    review_status: Mapped[str] = mapped_column(String(40), default="unreviewed")
    review_notes: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    portfolio_priority_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    event = relationship("Event", back_populates="alerts", lazy="selectin")
    company = relationship("Company", back_populates="alerts", lazy="selectin")
    portfolio_impacts = relationship(
        "AlertPortfolioImpact", back_populates="alert", lazy="selectin", cascade="all, delete-orphan"
    )


class AlertPortfolioImpact(Base):
    __tablename__ = "alert_portfolio_impacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id"))
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"))
    exposure_amount: Mapped[float] = mapped_column(Float, default=0.0)
    impact_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    alert = relationship("Alert", back_populates="portfolio_impacts")
    portfolio = relationship("Portfolio")
