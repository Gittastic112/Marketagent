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
        
from app.models import MarketPrice, Portfolio, PortfolioHolding
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
    
    # AAPL: 10 * 150 = 1500
    # MSFT: 5 * None = None
    assert val["total_market_value"] == 1500.0
    # Unrealized PNL = 1500 - 2000 = -500
    assert val["total_unrealized_pnl"] == -500.0

    # Check holdings
    assert len(val["holdings"]) == 2
    
    aapl_val = next(h for h in val["holdings"] if h["ticker"] == "AAPL")
    assert aapl_val["market_price"] == 150.0
    assert aapl_val["market_value"] == 1500.0
    assert aapl_val["total_cost"] == 1000.0
    assert aapl_val["unrealized_pnl"] == 500.0
    assert aapl_val["weight_percent"] == 100.0 # 100% of the total known market value

    msft_val = next(h for h in val["holdings"] if h["ticker"] == "MSFT")
    assert msft_val["market_price"] is None
    assert msft_val["market_value"] is None
    assert msft_val["total_cost"] == 1000.0
    assert msft_val["unrealized_pnl"] is None
    assert msft_val["weight_percent"] == 0.0


def test_calculate_portfolio_valuation_not_found(db: Session) -> None:
    with pytest.raises(ValueError, match="Portfolio 999 not found"):
        calculate_portfolio_valuation(db, 999)
