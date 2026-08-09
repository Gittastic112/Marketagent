from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ThesisNote(Base):
    __tablename__ = "thesis_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
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
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    importance: Mapped[str | None] = mapped_column(String(40), default="medium")
    original_confidence: Mapped[str] = mapped_column(String(40), default="medium")
    current_confidence: Mapped[str] = mapped_column(String(40), default="medium")
    status: Mapped[str] = mapped_column(String(40), default="active")
    last_reviewed: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    falsification_trigger: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_links: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    thesis_note = relationship("ThesisNote", back_populates="assumptions")
    impacts = relationship(
        "EventThesisImpact", back_populates="thesis_assumption", lazy="selectin", cascade="all, delete-orphan"
    )


class EventThesisImpact(Base):
    __tablename__ = "event_thesis_impacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    thesis_assumption_id: Mapped[int] = mapped_column(ForeignKey("thesis_assumptions.id", ondelete="CASCADE"), index=True)
    impact_classification: Mapped[str] = mapped_column(String(40))  # e.g., "Supports", "Weakens", "Invalidates", "Neutral"
    rationale: Mapped[str] = mapped_column(Text)

    # Evidence Ledger Fields (Stage 7)
    claim: Mapped[str | None] = mapped_column(Text, nullable=True)
    importance: Mapped[str] = mapped_column(String(40), default="medium")
    confidence: Mapped[str] = mapped_column(String(40), default="medium")
    review_status: Mapped[str] = mapped_column(String(40), default="unreviewed")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    thesis_assumption = relationship("ThesisAssumption", back_populates="impacts")
    event = relationship("Event", back_populates="thesis_impacts", lazy="selectin")

class ThesisChange(Base):
    __tablename__ = "thesis_changes"

    id: Mapped[int] = mapped_column(primary_key=True)
    thesis_note_id: Mapped[int] = mapped_column(ForeignKey("thesis_notes.id"))
    change_summary: Mapped[str] = mapped_column(Text)
    drift_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    thesis_note = relationship("ThesisNote", back_populates="changes")
