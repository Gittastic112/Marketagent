from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    sector: Mapped[str | None] = mapped_column(String(120))
    industry: Mapped[str | None] = mapped_column(String(120))
    exchange: Mapped[str | None] = mapped_column(String(80))
    cik: Mapped[str | None] = mapped_column(String(20), unique=True)
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    raw_documents = relationship("RawDocument", back_populates="company", lazy="selectin")
    events = relationship("Event", back_populates="company", lazy="selectin")
    alerts = relationship("Alert", back_populates="company", lazy="selectin")
    thesis_notes = relationship("ThesisNote", back_populates="company", lazy="selectin")
