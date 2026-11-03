from datetime import date, datetime, UTC
from typing import Any

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, DateTime, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PeerValuationSet(Base):
    __tablename__ = "peer_valuation_sets"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "company_id",
            "import_sha256",
            name="uq_peer_valuation_sets_owner_company_import_sha256",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    name: Mapped[str] = mapped_column(String(120))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Reviewed member facts remain together so their per-member source evidence is
    # never detached from the multiple supplied by the user.
    peer_identifiers_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    target_context_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    import_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Pre-calculated aggregates for the peer set (e.g. median EV/EBITDA, mean P/E)
    aggregate_metrics_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    aggregation_method: Mapped[str] = mapped_column(String(20), default="median")
    version: Mapped[int] = mapped_column(Integer, default=1)
    review_status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    review_diagnostics_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    review_warning_codes_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    review_diagnostics_as_of: Mapped[date | None] = mapped_column(Date, nullable=True)

    notes: Mapped[str | None] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    company = relationship("Company")
    revisions = relationship(
        "PeerValuationSetRevision",
        back_populates="peer_set",
        cascade="all, delete-orphan",
        order_by="PeerValuationSetRevision.version",
    )
    member_records = relationship(
        "PeerValuationMemberRecord",
        back_populates="peer_set",
        cascade="all, delete-orphan",
        order_by="PeerValuationMemberRecord.ordinal",
    )
    target_profile = relationship(
        "PeerValuationTargetProfile",
        back_populates="peer_set",
        cascade="all, delete-orphan",
        uselist=False,
    )


class PeerValuationSetRevision(Base):
    __tablename__ = "peer_valuation_set_revisions"
    __table_args__ = (
        UniqueConstraint(
            "peer_set_id",
            "version",
            name="uq_peer_valuation_set_revisions_set_version",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    peer_set_id: Mapped[int] = mapped_column(
        ForeignKey("peer_valuation_sets.id", ondelete="CASCADE"),
        index=True,
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(30), index=True)
    changed_fields_json: Mapped[list[str]] = mapped_column(JSON, default=list)

    name: Mapped[str] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean)
    review_status: Mapped[str] = mapped_column(String(20))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    review_diagnostics_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    review_warning_codes_json: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    review_diagnostics_as_of: Mapped[date | None] = mapped_column(Date, nullable=True)
    aggregation_method: Mapped[str] = mapped_column(String(20))
    members_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    target_context_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    aggregate_metrics_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    peer_set = relationship("PeerValuationSet", back_populates="revisions")
    member_records = relationship(
        "PeerValuationRevisionMemberRecord",
        back_populates="revision",
        cascade="all, delete-orphan",
        order_by="PeerValuationRevisionMemberRecord.ordinal",
    )
    target_profile = relationship(
        "PeerValuationRevisionTargetProfile",
        back_populates="revision",
        cascade="all, delete-orphan",
        uselist=False,
    )


class PeerValuationMemberRecord(Base):
    __tablename__ = "peer_valuation_members"
    __table_args__ = (
        UniqueConstraint("peer_set_id", "ordinal", name="uq_peer_valuation_members_set_ordinal"),
        UniqueConstraint("peer_set_id", "identifier", name="uq_peer_valuation_members_set_identifier"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    peer_set_id: Mapped[int] = mapped_column(
        ForeignKey("peer_valuation_sets.id", ondelete="CASCADE"), index=True
    )
    ordinal: Mapped[int] = mapped_column(Integer)
    identifier: Mapped[str] = mapped_column(String(80), index=True)
    peer_company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    included: Mapped[bool] = mapped_column(Boolean, default=True)
    pe: Mapped[float | None] = mapped_column(Float, nullable=True)
    pbv: Mapped[float | None] = mapped_column(Float, nullable=True)
    ps: Mapped[float | None] = mapped_column(Float, nullable=True)
    ev_sales: Mapped[float | None] = mapped_column(Float, nullable=True)
    ev_ebitda: Mapped[float | None] = mapped_column(Float, nullable=True)
    ev_ebit: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    source_as_of: Mapped[date | None] = mapped_column(Date, nullable=True)
    claim_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    fiscal_period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    accounting_standard: Mapped[str | None] = mapped_column(String(40), nullable=True)
    market_cap: Mapped[float | None] = mapped_column(Float, nullable=True)
    revenue_growth_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    ebitda_margin_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    peer_set = relationship("PeerValuationSet", back_populates="member_records")


class PeerValuationRevisionMemberRecord(Base):
    __tablename__ = "peer_valuation_revision_members"
    __table_args__ = (
        UniqueConstraint("revision_id", "ordinal", name="uq_peer_revision_members_revision_ordinal"),
        UniqueConstraint("revision_id", "identifier", name="uq_peer_revision_members_revision_identifier"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    revision_id: Mapped[int] = mapped_column(
        ForeignKey("peer_valuation_set_revisions.id", ondelete="CASCADE"), index=True
    )
    ordinal: Mapped[int] = mapped_column(Integer)
    identifier: Mapped[str] = mapped_column(String(80), index=True)
    peer_company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    included: Mapped[bool] = mapped_column(Boolean)
    pe: Mapped[float | None] = mapped_column(Float, nullable=True)
    pbv: Mapped[float | None] = mapped_column(Float, nullable=True)
    ps: Mapped[float | None] = mapped_column(Float, nullable=True)
    ev_sales: Mapped[float | None] = mapped_column(Float, nullable=True)
    ev_ebitda: Mapped[float | None] = mapped_column(Float, nullable=True)
    ev_ebit: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    source_as_of: Mapped[date | None] = mapped_column(Date, nullable=True)
    claim_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    fiscal_period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    accounting_standard: Mapped[str | None] = mapped_column(String(40), nullable=True)
    market_cap: Mapped[float | None] = mapped_column(Float, nullable=True)
    revenue_growth_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    ebitda_margin_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    revision = relationship("PeerValuationSetRevision", back_populates="member_records")


class PeerValuationTargetProfile(Base):
    __tablename__ = "peer_valuation_target_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    peer_set_id: Mapped[int] = mapped_column(
        ForeignKey("peer_valuation_sets.id", ondelete="CASCADE"), unique=True, index=True
    )
    source_name: Mapped[str] = mapped_column(String(160))
    source_url: Mapped[str] = mapped_column(String(2048))
    source_as_of: Mapped[date] = mapped_column(Date)
    claim_type: Mapped[str] = mapped_column(String(30))
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    fiscal_period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    accounting_standard: Mapped[str | None] = mapped_column(String(40), nullable=True)
    market_cap: Mapped[float | None] = mapped_column(Float, nullable=True)
    revenue_growth_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    ebitda_margin_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    peer_set = relationship("PeerValuationSet", back_populates="target_profile")


class PeerValuationRevisionTargetProfile(Base):
    __tablename__ = "peer_valuation_revision_target_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    revision_id: Mapped[int] = mapped_column(
        ForeignKey("peer_valuation_set_revisions.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    source_name: Mapped[str] = mapped_column(String(160))
    source_url: Mapped[str] = mapped_column(String(2048))
    source_as_of: Mapped[date] = mapped_column(Date)
    claim_type: Mapped[str] = mapped_column(String(30))
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    fiscal_period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    accounting_standard: Mapped[str | None] = mapped_column(String(40), nullable=True)
    market_cap: Mapped[float | None] = mapped_column(Float, nullable=True)
    revenue_growth_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    ebitda_margin_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    revision = relationship("PeerValuationSetRevision", back_populates="target_profile")
