from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class NarrativeCluster(Base):
    __tablename__ = "narrative_clusters"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)

    # Stage 11: Narrative Intelligence metadata
    first_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    velocity: Mapped[float | None] = mapped_column(Float, nullable=True) # E.g., mentions per day
    source_diversity: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="Emerging") # Emerging, Strengthening, Stable, Weakening, Contradicted, Dormant

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    claims: Mapped[list["NarrativeClaim"]] = relationship("NarrativeClaim", back_populates="cluster", cascade="all, delete-orphan")
    mentions: Mapped[list["NarrativeMention"]] = relationship("NarrativeMention", back_populates="cluster", cascade="all, delete-orphan")


class NarrativeClaim(Base):
    __tablename__ = "narrative_claims"

    id: Mapped[int] = mapped_column(primary_key=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("narrative_clusters.id"), index=True)
    claim_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    cluster: Mapped["NarrativeCluster"] = relationship("NarrativeCluster", back_populates="claims")


class NarrativeMention(Base):
    __tablename__ = "narrative_mentions"

    id: Mapped[int] = mapped_column(primary_key=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("narrative_clusters.id"), index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), index=True)
    context_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    cluster: Mapped["NarrativeCluster"] = relationship("NarrativeCluster", back_populates="mentions")
    event = relationship("Event", back_populates="narrative_mentions")
