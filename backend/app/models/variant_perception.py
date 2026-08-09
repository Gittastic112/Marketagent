from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class VariantPerception(Base):
    __tablename__ = "variant_perception"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))

    market_belief: Mapped[str] = mapped_column(Text)
    my_belief: Mapped[str] = mapped_column(Text)

    evidence_for_my_belief: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_against_my_belief: Mapped[str | None] = mapped_column(Text, nullable=True)

    how_price_reflects_market_belief: Mapped[str | None] = mapped_column(Text, nullable=True)
    what_would_close_the_gap: Mapped[str | None] = mapped_column(Text, nullable=True)

    confidence: Mapped[str] = mapped_column(String(40), default="medium")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    company = relationship("Company", backref="variant_perceptions", lazy="selectin")
