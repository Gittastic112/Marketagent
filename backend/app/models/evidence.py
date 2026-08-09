from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EvidenceLedgerItem(Base):
    __tablename__ = "evidence_ledger"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    evidence_text: Mapped[str] = mapped_column(Text)
    effect: Mapped[str] = mapped_column(String(40))  # Supports, Weakens, Contradicts, Neutral
    source_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    confidence: Mapped[str] = mapped_column(String(40), default="medium")
    date_discovered: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    company = relationship("Company", backref="evidence_items", lazy="selectin")
