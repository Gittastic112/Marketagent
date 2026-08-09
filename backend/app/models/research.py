from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class ResearchSession(Base):
    __tablename__ = "research_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    messages: Mapped[list["ResearchMessage"]] = relationship(
        "ResearchMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ResearchMessage.created_at"
    )


class ResearchMessage(Base):
    __tablename__ = "research_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False)
    ai_output_id: Mapped[int | None] = mapped_column(ForeignKey("ai_outputs.id", ondelete="SET NULL"), nullable=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # "user" or "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["ResearchSession"] = relationship("ResearchSession", back_populates="messages")
    ai_output: Mapped["AiOutput"] = relationship("AiOutput", lazy="joined")
