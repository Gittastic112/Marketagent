from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"))
    raw_document_id: Mapped[int | None] = mapped_column(ForeignKey("raw_documents.id"))
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    information_speed: Mapped[str] = mapped_column(String(20), index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    event_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    credibility_score: Mapped[int | None] = mapped_column()
    novelty_score: Mapped[int | None] = mapped_column()
    impact_score: Mapped[int | None] = mapped_column()
    priority_score: Mapped[int | None] = mapped_column()
    score_explanation_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company", back_populates="events", lazy="selectin")
    raw_document = relationship("RawDocument", back_populates="events", lazy="selectin")
    alerts = relationship("Alert", back_populates="event", lazy="selectin")

    corroborates = relationship(
        "Event",
        secondary="event_corroborations",
        primaryjoin="Event.id == EventCorroboration.source_event_id",
        secondaryjoin="Event.id == EventCorroboration.target_event_id",
        lazy="selectin",
        viewonly=True
    )
    contradicts = relationship(
        "Event",
        secondary="event_contradictions",
        primaryjoin="Event.id == EventContradiction.source_event_id",
        secondaryjoin="Event.id == EventContradiction.target_event_id",
        lazy="selectin",
        viewonly=True
    )


class EventCorroboration(Base):
    __tablename__ = "event_corroborations"
    
    source_event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), primary_key=True)
    target_event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EventContradiction(Base):
    __tablename__ = "event_contradictions"
    
    source_event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), primary_key=True)
    target_event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
