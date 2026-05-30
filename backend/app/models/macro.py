from datetime import date
from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class MacroSeries(Base):
    __tablename__ = "macro_series"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    units: Mapped[str | None] = mapped_column(String, nullable=True)
    frequency: Mapped[str | None] = mapped_column(String, nullable=True)

    observations: Mapped[list["MacroObservation"]] = relationship(
        "MacroObservation", back_populates="series", cascade="all, delete-orphan"
    )

class MacroObservation(Base):
    __tablename__ = "macro_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    series_id: Mapped[int] = mapped_column(ForeignKey("macro_series.id"), index=True)
    date_recorded: Mapped[date] = mapped_column(Date, index=True)
    value: Mapped[float] = mapped_column(Float)

    series: Mapped["MacroSeries"] = relationship("MacroSeries", back_populates="observations")
