from collections.abc import Generator
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.engine import Engine

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Company, MarketPrice, Portfolio, PortfolioCashBalance, PortfolioHolding
from app.services.portfolio_analytics import calculate_portfolio_analytics

@pytest.fixture
def engine() -> Generator[Engine]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db(engine: Engine) -> Generator[Session]:
    with Session(engine) as session:
        yield session


@pytest.fixture
def client(engine: Engine) -> Generator[TestClient]:
    def override_get_db() -> Generator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_calculate_portfolio_analytics(db: Session, client: TestClient):
    # Setup Data
    portfolio = Portfolio(name="Analytics Test Portfolio", base_currency="USD")
    db.add(portfolio)
    db.commit()

    company1 = Company(ticker="AAPL", name="Apple Inc.", sector="Technology", country="USA", asset_type="Equity")
    company2 = Company(ticker="MSFT", name="Microsoft Corp.", sector="Technology", country="USA", asset_type="Equity")
    company3 = Company(ticker="BHP", name="BHP Group", sector="Materials", country="Australia", asset_type="Equity")
    db.add_all([company1, company2, company3])
    db.commit()

    holding1 = PortfolioHolding(
        portfolio_id=portfolio.id, company_id=company1.id, ticker="AAPL", quantity=10, average_cost=150, as_of_date=date(2026, 1, 1)
    )
    holding2 = PortfolioHolding(
        portfolio_id=portfolio.id, company_id=company2.id, ticker="MSFT", quantity=5, average_cost=300, as_of_date=date(2026, 1, 1)
    )
    holding3 = PortfolioHolding(
        portfolio_id=portfolio.id, company_id=company3.id, ticker="BHP", quantity=20, average_cost=50, as_of_date=date(2026, 1, 1)
    )
    db.add_all([holding1, holding2, holding3])

    cash = PortfolioCashBalance(
        portfolio_id=portfolio.id, currency="USD", amount=5000.0, as_of_date=date(2026, 5, 24)
    )
    db.add(cash)

    price1 = MarketPrice(company_id=company1.id, ticker="AAPL", price=200, as_of_date=date(2026, 5, 24))  # MV: 2000
    price2 = MarketPrice(company_id=company2.id, ticker="MSFT", price=400, as_of_date=date(2026, 5, 24))  # MV: 2000
    price3 = MarketPrice(company_id=company3.id, ticker="BHP", price=40, as_of_date=date(2026, 5, 24))    # MV: 800 (Total MV: 4800)
    db.add_all([price1, price2, price3])
    db.commit()

    # Call Service
    analytics = calculate_portfolio_analytics(db, portfolio.id, as_of_date=date(2026, 5, 24))

    # Assertions
    assert analytics["total_invested_value"] == 4800.0
    assert analytics["total_cash_value"] == 5000.0
    assert analytics["total_portfolio_value"] == 9800.0

    # Sector Exposure (Technology: 4000/4800 = ~83.3%, Materials: 800/4800 = ~16.7%)
    # Wait, the analytics service aggregates weights, and weights are based on total invested value.
    # AAPL weight: 2000/4800 = 41.666%
    # MSFT weight: 2000/4800 = 41.666%
    # BHP weight: 800/4800 = 16.666%
    assert round(analytics["sector_exposure"]["Technology"], 2) == 83.33
    assert round(analytics["sector_exposure"]["Materials"], 2) == 16.67
    
    assert round(analytics["country_exposure"]["USA"], 2) == 83.33
    assert round(analytics["country_exposure"]["Australia"], 2) == 16.67

    # Top Gainers/Losers
    # AAPL PNL = 2000 - 1500 = 500
    # MSFT PNL = 2000 - 1500 = 500
    # BHP PNL = 800 - 1000 = -200
    assert analytics["top_gainers"][0]["ticker"] in ["AAPL", "MSFT"]
    assert analytics["top_losers"][0]["ticker"] == "BHP"

    # Concentration
    # HHI = (0.4166)^2 + (0.4166)^2 + (0.1666)^2 = 0.1736 + 0.1736 + 0.0277 = 0.375
    assert round(analytics["concentration_score"], 3) == 0.375

    # Warnings
    warnings = analytics["diversification_warnings"]
    assert any("High concentration" in w for w in warnings)
    assert any("Low diversification" in w for w in warnings)
    assert any("HHI" in w for w in warnings)

    # API Endpoint Test
    response = client.get(f"/portfolios/{portfolio.id}/analytics?as_of_date=2026-05-24")
    assert response.status_code == 200
    data = response.json()
    assert data["total_portfolio_value"] == 9800.0
    assert data["concentration_score"] is not None
