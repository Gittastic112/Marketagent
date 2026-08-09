import pytest
from datetime import date
from sqlalchemy.orm import Session
from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from app.db.base import Base

@pytest.fixture
def db() -> Generator[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

from app.models import Alert, Company, MarketPrice, Portfolio, PortfolioHolding
from app.services.portfolio_valuation import calculate_portfolio_valuation


def test_calculate_portfolio_valuation(db: Session) -> None:
    # Setup test data
    portfolio = Portfolio(name="Test Portfolio", base_currency="USD")
    db.add(portfolio)
    db.commit()

    holding1 = PortfolioHolding(
        portfolio_id=portfolio.id,
        ticker="AAPL",
        quantity=10,
        average_cost=100.0, # Total cost = 1000
        currency="USD",
        as_of_date=date(2026, 5, 27)
    )
    holding2 = PortfolioHolding(
        portfolio_id=portfolio.id,
        ticker="MSFT",
        quantity=5,
        average_cost=200.0, # Total cost = 1000
        currency="USD",
        as_of_date=date(2026, 5, 27)
    )
    db.add_all([holding1, holding2])
    db.commit()

    # Add market prices
    mp1 = MarketPrice(ticker="AAPL", price=150.0, currency="USD", as_of_date=date(2026, 5, 28))
    # MSFT price is missing
    db.add_all([mp1])
    db.commit()

    # Calculate valuation
    val = calculate_portfolio_valuation(db, portfolio.id, as_of_date=date(2026, 5, 28))

    assert val["portfolio_id"] == portfolio.id
    assert val["total_cost_basis"] == 2000.0

    # Aggregate valuation remains unavailable until every active holding has a price.
    assert val["total_market_value"] is None
    assert val["total_unrealized_pnl"] is None
    assert val["total_portfolio_value"] is None

    # Check holdings
    assert len(val["holdings"]) == 2

    aapl_val = next(h for h in val["holdings"] if h["ticker"] == "AAPL")
    assert aapl_val["market_price"] == 150.0
    assert aapl_val["market_value"] == 1500.0
    assert aapl_val["total_cost"] == 1000.0
    assert aapl_val["unrealized_pnl"] == 500.0
    assert aapl_val["weight_percent"] is None

    msft_val = next(h for h in val["holdings"] if h["ticker"] == "MSFT")
    assert msft_val["market_price"] is None
    assert msft_val["market_value"] is None
    assert msft_val["total_cost"] == 1000.0
    assert msft_val["unrealized_pnl"] is None
    assert msft_val["weight_percent"] is None


def test_cash_only_portfolio_has_a_total_value(db: Session) -> None:
    from app.models import PortfolioCashBalance

    portfolio = Portfolio(name="Cash Portfolio", base_currency="USD")
    db.add(portfolio)
    db.flush()
    db.add(
        PortfolioCashBalance(
            portfolio_id=portfolio.id,
            currency="USD",
            amount=2500,
            as_of_date=date(2026, 5, 28),
        )
    )
    db.commit()

    valuation = calculate_portfolio_valuation(
        db,
        portfolio.id,
        as_of_date=date(2026, 5, 28),
    )

    assert valuation["total_market_value"] is None
    assert valuation["total_portfolio_value"] == 2500
    assert valuation["total_cash_value"] == 2500


def test_active_alert_count_is_scoped_to_user(db: Session) -> None:
    portfolio = Portfolio(name="Alert Portfolio", base_currency="USD")
    company = Company(ticker="AAPL", name="Apple")
    holding = PortfolioHolding(
        portfolio=portfolio,
        company=company,
        ticker="AAPL",
        quantity=1,
        average_cost=100,
        currency="USD",
        as_of_date=date(2026, 5, 28),
    )
    db.add_all(
        [
            portfolio,
            company,
            holding,
            MarketPrice(
                ticker="AAPL",
                price=110,
                currency="USD",
                as_of_date=date(2026, 5, 28),
            ),
            Alert(
                user_id="owner-user",
                alert_type="filing",
                severity="medium",
                title="Owner alert",
                company=company,
            ),
            Alert(
                user_id="other-user",
                alert_type="filing",
                severity="medium",
                title="Other alert",
                company=company,
            ),
        ]
    )
    db.commit()

    owner_valuation = calculate_portfolio_valuation(
        db,
        portfolio.id,
        as_of_date=date(2026, 5, 28),
        user_id="owner-user",
    )

    assert owner_valuation["holdings"][0]["active_alerts_count"] == 1


def test_calculate_portfolio_valuation_not_found(db: Session) -> None:
    with pytest.raises(ValueError, match="Portfolio 999 not found"):
        calculate_portfolio_valuation(db, 999)
