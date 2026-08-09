from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Date, DateTime, ForeignKey, JSON, Numeric, String, Text, func
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

    holdings = relationship("PortfolioHolding", back_populates="portfolio", lazy="selectin")
    transactions = relationship("PortfolioTransaction", back_populates="portfolio", lazy="selectin")
    cash_balances = relationship("PortfolioCashBalance", back_populates="portfolio", lazy="selectin")
    snapshots = relationship("PortfolioSnapshot", back_populates="portfolio", lazy="selectin")


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

    portfolio = relationship("Portfolio", back_populates="holdings", lazy="selectin")
    company = relationship("Company", back_populates="portfolio_holdings", lazy="selectin")


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

    portfolio = relationship("Portfolio", back_populates="transactions", lazy="selectin")
    company = relationship("Company", back_populates="portfolio_transactions", lazy="selectin")


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

    portfolio = relationship("Portfolio", back_populates="cash_balances", lazy="selectin")


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, index=True)
    total_market_value: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    total_cost_basis: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    total_cash: Mapped[Decimal | None] = mapped_column(Numeric(20, 6))
    payload_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    portfolio = relationship("Portfolio", back_populates="snapshots", lazy="selectin")
