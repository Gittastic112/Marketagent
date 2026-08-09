from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FilingSection(Base):
    __tablename__ = "filing_sections"

    id: Mapped[int] = mapped_column(primary_key=True)
    raw_document_id: Mapped[int] = mapped_column(ForeignKey("raw_documents.id", ondelete="CASCADE"), index=True)
    item_name: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str | None] = mapped_column(String(500))
    text_content: Mapped[str] = mapped_column(Text)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    raw_document = relationship("RawDocument", backref="sections", lazy="selectin")
    # A section can have diffs where it is the current section
    diffs_as_current = relationship("FilingSectionDiff", foreign_keys="[FilingSectionDiff.current_section_id]", back_populates="current_section", cascade="all, delete-orphan", lazy="selectin")
    # A section can have diffs where it is the prior section
    diffs_as_prior = relationship("FilingSectionDiff", foreign_keys="[FilingSectionDiff.prior_section_id]", back_populates="prior_section", cascade="all, delete-orphan")


class FilingSectionDiff(Base):
    __tablename__ = "filing_section_diffs"

    id: Mapped[int] = mapped_column(primary_key=True)
    current_section_id: Mapped[int] = mapped_column(ForeignKey("filing_sections.id", ondelete="CASCADE"), index=True)
    prior_section_id: Mapped[int | None] = mapped_column(ForeignKey("filing_sections.id", ondelete="SET NULL"), index=True)

    added_words: Mapped[int] = mapped_column(Integer, default=0)
    removed_words: Mapped[int] = mapped_column(Integer, default=0)
    diff_html: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    current_section = relationship("FilingSection", foreign_keys=[current_section_id], back_populates="diffs_as_current")
    prior_section = relationship("FilingSection", foreign_keys=[prior_section_id], back_populates="diffs_as_prior")
