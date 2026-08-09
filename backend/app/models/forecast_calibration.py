from datetime import datetime, UTC

from sqlalchemy import Float, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ForecastCalibration(Base):
    __tablename__ = "forecast_calibrations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    valuation_model_id: Mapped[int | None] = mapped_column(ForeignKey("valuation_models.id", ondelete="SET NULL"), nullable=True)
    event_id: Mapped[int | None] = mapped_column(ForeignKey("events.id", ondelete="SET NULL"), nullable=True)

    metric_name: Mapped[str] = mapped_column(String(120), index=True)
    forecast_value: Mapped[float] = mapped_column(Float)
    actual_value: Mapped[float] = mapped_column(Float)
    error_margin: Mapped[float] = mapped_column(Float)

    forecast_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actual_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    interpretation: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    company = relationship("Company")
    valuation_model = relationship("ValuationModel")
    event = relationship("Event")
