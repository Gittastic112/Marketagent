from datetime import UTC, date, datetime

from sqlalchemy import Date, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class CompanyIndustryMix(Base):
    __tablename__ = "company_industry_mixes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    basis: Mapped[str] = mapped_column(String(40), default="revenue")
    as_of_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_document_id: Mapped[int | None] = mapped_column(
        ForeignKey("raw_documents.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(default=utc_now, onupdate=utc_now)

    company = relationship("Company")
    source_document = relationship("RawDocument")
    allocations = relationship(
        "CompanyIndustryAllocation",
        back_populates="mix",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="CompanyIndustryAllocation.id",
    )


class CompanyIndustryAllocation(Base):
    __tablename__ = "company_industry_allocations"
    __table_args__ = (
        UniqueConstraint("mix_id", "segment_name", name="uq_company_industry_allocation_segment"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    mix_id: Mapped[int] = mapped_column(
        ForeignKey("company_industry_mixes.id", ondelete="CASCADE"),
        index=True,
    )
    segment_name: Mapped[str] = mapped_column(String(120))
    industry_name: Mapped[str] = mapped_column(String(255), index=True)
    weight_percent: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(default=utc_now, onupdate=utc_now)

    mix = relationship("CompanyIndustryMix", back_populates="allocations")
