from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SocialPost(Base):
    __tablename__ = "social_posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    platform: Mapped[str] = mapped_column(String(50), index=True)
    source_url: Mapped[str] = mapped_column(Text)
    author: Mapped[str | None] = mapped_column(String(100))
    raw_text: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payload_json: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    sentiment_scores: Mapped[list["SentimentScore"]] = relationship("SentimentScore", back_populates="post", cascade="all, delete-orphan")
    narrative_mentions: Mapped[list["NarrativeMention"]] = relationship("NarrativeMention", back_populates="post", cascade="all, delete-orphan")


class SentimentScore(Base):
    __tablename__ = "sentiment_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int | None] = mapped_column(ForeignKey("social_posts.id"), index=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), index=True)
    score: Mapped[str] = mapped_column(String(50))  # e.g., 'Bullish', 'Bearish', 'Neutral'
    rationale: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    post: Mapped["SocialPost"] = relationship("SocialPost", back_populates="sentiment_scores")


class NarrativeCluster(Base):
    __tablename__ = "narrative_clusters"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
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
    post_id: Mapped[int] = mapped_column(ForeignKey("social_posts.id"), index=True)
    context_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    cluster: Mapped["NarrativeCluster"] = relationship("NarrativeCluster", back_populates="mentions")
    post: Mapped["SocialPost"] = relationship("SocialPost", back_populates="narrative_mentions")
