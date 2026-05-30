from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AiOutput(Base):
    __tablename__ = "ai_outputs"

    id: Mapped[int] = mapped_column(primary_key=True)
    raw_document_id: Mapped[int] = mapped_column(ForeignKey("raw_documents.id", ondelete="CASCADE"), index=True)
    
    model_name: Mapped[str] = mapped_column(String(100))
    prompt_version: Mapped[str] = mapped_column(String(50))
    input_hash: Mapped[str] = mapped_column(String(128))
    
    output_text: Mapped[str] = mapped_column(Text)
    limitations: Mapped[str | None] = mapped_column(Text)
    confidence_label: Mapped[str] = mapped_column(String(50))
    human_review_status: Mapped[str] = mapped_column(String(50), default="pending")
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    raw_document = relationship("RawDocument", backref="ai_outputs", lazy="selectin")
