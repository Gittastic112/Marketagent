from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company = relationship("Company", back_populates="events", lazy="selectin")
    raw_document = relationship("RawDocument", back_populates="events", lazy="selectin")
    alerts = relationship("Alert", back_populates="event", lazy="selectin")
