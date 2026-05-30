from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ThesisNote(Base):
    __tablename__ = "thesis_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    title: Mapped[str] = mapped_column(String(500))
    thesis_text: Mapped[str] = mapped_column(Text)
    assumptions_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(40), default="active")
    thesis_drift_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    company = relationship("Company", back_populates="thesis_notes", lazy="selectin")
    assumptions = relationship(
        "ThesisAssumption", back_populates="thesis_note", lazy="selectin", cascade="all, delete-orphan"
    )
    changes = relationship(
        "ThesisChange", back_populates="thesis_note", lazy="selectin", cascade="all, delete-orphan"
    )


class ThesisAssumption(Base):
    __tablename__ = "thesis_assumptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    thesis_note_id: Mapped[int] = mapped_column(ForeignKey("thesis_notes.id"))
    description: Mapped[str] = mapped_column(Text)
    original_confidence: Mapped[str] = mapped_column(String(40), default="medium")
    current_confidence: Mapped[str] = mapped_column(String(40), default="medium")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    thesis_note = relationship("ThesisNote", back_populates="assumptions")


class ThesisChange(Base):
    __tablename__ = "thesis_changes"

    id: Mapped[int] = mapped_column(primary_key=True)
    thesis_note_id: Mapped[int] = mapped_column(ForeignKey("thesis_notes.id"))
    change_summary: Mapped[str] = mapped_column(Text)
    drift_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    thesis_note = relationship("ThesisNote", back_populates="changes")
