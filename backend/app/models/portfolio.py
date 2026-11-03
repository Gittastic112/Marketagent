from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, JSON, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True)
    base_currency: Mapped[str] = mapped_column(String(10), default="USD")
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Flat ownership/identity reads must not fetch financial history. Services
    # declare their read graph explicitly when they need related records.
    holdings = relationship("PortfolioHolding", back_populates="portfolio", lazy="select")
    transactions = relationship("PortfolioTransaction", back_populates="portfolio", lazy="select")
    cash_balances = relationship("PortfolioCashBalance", back_populates="portfolio", lazy="select")
    snapshots = relationship("PortfolioSnapshot", back_populates="portfolio", lazy="select")
    benchmark_config = relationship(
        "PortfolioBenchmarkConfig",
        back_populates="portfolio",
        cascade="all, delete-orphan",
        lazy="select",
        uselist=False,
    )


class PortfolioBenchmarkConfig(Base):
    __tablename__ = "portfolio_benchmark_configs"
    __table_args__ = (
        UniqueConstraint("portfolio_id", name="uq_portfolio_benchmark_configs_portfolio"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    benchmark_company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    ticker: Mapped[str] = mapped_column(String(40), index=True)
    currency: Mapped[str] = mapped_column(String(10))
    provider_name: Mapped[str] = mapped_column(String(80), default="manual")
    provider_symbol: Mapped[str | None] = mapped_column(String(80), nullable=True)
    effective_from: Mapped[date] = mapped_column(Date)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    portfolio = relationship("Portfolio", back_populates="benchmark_config", lazy="select")


class PortfolioHolding(Base):
    __tablename__ = "portfolio_holdings"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), index=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), index=True)
    ticker: Mapped[str] = mapped_column(String(20), index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    average_cost: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=0)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    as_of_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    portfolio = relationship("Portfolio", back_populates="holdings", lazy="select")
    company = relationship("Company", back_populates="portfolio_holdings", lazy="select")


class PortfolioTransaction(Base):
    __tablename__ = "portfolio_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), index=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), index=True)
    ticker: Mapped[str] = mapped_column(String(20), index=True)
    transaction_type: Mapped[str] = mapped_column(String(40), index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    price: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=0)
    fees: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=0)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    transaction_date: Mapped[date] = mapped_column(Date, index=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    portfolio = relationship("Portfolio", back_populates="transactions", lazy="select")
    company = relationship("Company", back_populates="portfolio_transactions", lazy="select")


class PortfolioCashBalance(Base):
    __tablename__ = "portfolio_cash_balances"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), index=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 6), default=0)
    as_of_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    portfolio = relationship("Portfolio", back_populates="cash_balances", lazy="select")


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"
    __table_args__ = (
        UniqueConstraint("portfolio_id", "snapshot_date", name="uq_portfolio_snapshots_portfolio_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, index=True)
    total_market_value: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    total_cost_basis: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    total_cash: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    total_portfolio_value: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    base_currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    calculation_status: Mapped[str] = mapped_column(String(30), default="not_available")
    holdings_count: Mapped[int] = mapped_column(default=0)
    priced_holdings_count: Mapped[int] = mapped_column(default=0)
    missing_price_tickers_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    missing_fx_pairs_json: Mapped[list[str]] = mapped_column(JSON, default=list)
    payload_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    portfolio = relationship("Portfolio", back_populates="snapshots", lazy="select")
