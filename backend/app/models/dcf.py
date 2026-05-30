from datetime import datetime
from typing import Any, Optional

from sqlalchemy import ForeignKey, String, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ValuationModel(Base):
    __tablename__ = "valuation_models"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company")
    assumption_sets = relationship("DcfAssumptionSet", back_populates="valuation_model", cascade="all, delete-orphan")


class DcfAssumptionSet(Base):
    __tablename__ = "dcf_assumption_sets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    valuation_model_id: Mapped[int] = mapped_column(ForeignKey("valuation_models.id", ondelete="CASCADE"), index=True)
    scenario: Mapped[str] = mapped_column(String, default="Base") # Base, Bull, Bear
    discount_rate: Mapped[float] = mapped_column(Float) # WACC
    terminal_growth_rate: Mapped[float] = mapped_column(Float)
    projection_years: Mapped[int] = mapped_column(default=5)
    assumptions_json: Mapped[dict[str, Any]] = mapped_column(JSON) # e.g. growth rates, margins, tax rate, shares, debt

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    valuation_model = relationship("ValuationModel", back_populates="assumption_sets")
    outputs = relationship("DcfOutput", back_populates="assumption_set", cascade="all, delete-orphan")


class DcfOutput(Base):
    __tablename__ = "dcf_outputs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    assumption_set_id: Mapped[int] = mapped_column(ForeignKey("dcf_assumption_sets.id", ondelete="CASCADE"), index=True)
    enterprise_value: Mapped[float] = mapped_column(Float)
    equity_value: Mapped[float] = mapped_column(Float)
    implied_share_price: Mapped[float] = mapped_column(Float)
    output_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True) # Full projected cash flows

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    assumption_set = relationship("DcfAssumptionSet", back_populates="outputs")
