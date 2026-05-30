from datetime import date
from decimal import Decimal

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import PortfolioCashBalance

@pytest.fixture
def client() -> Generator[TestClient]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    def override_get_db() -> Generator[Session]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

def test_portfolio_cash_balance_sync_on_buy(client: TestClient):
    # Create portfolio
    response = client.post("/portfolios", json={"name": "Cash Sync Portfolio"})
    assert response.status_code == 201
    portfolio_id = response.json()["id"]

    # Post a buy transaction
    buy_payload = {
        "portfolio_id": portfolio_id,
        "ticker": "AAPL",
        "transaction_type": "buy",
        "quantity": 10.0,
        "price": 150.0,
        "fees": 5.0,
        "currency": "USD",
        "transaction_date": "2026-05-01"
    }
    response = client.post("/portfolio-transactions", json=buy_payload)
    assert response.status_code == 201

    # Check cash balance
    response = client.get(f"/portfolio-cash-balances?portfolio_id={portfolio_id}")
    assert response.status_code == 200
    balances = response.json()
    assert len(balances) == 1
    assert balances[0]["currency"] == "USD"
    # Buy 10 @ 150 + 5 fees = -1505
    assert Decimal(balances[0]["amount"]) == Decimal("-1505.0")


def test_portfolio_cash_balance_sync_on_deposit_and_sell(client: TestClient):
    # Create portfolio
    response = client.post("/portfolios", json={"name": "Cash Sync Portfolio 2"})
    assert response.status_code == 201
    portfolio_id = response.json()["id"]

    # Deposit
    deposit_payload = {
        "portfolio_id": portfolio_id,
        "ticker": "CASH",
        "transaction_type": "deposit",
        "quantity": 10000.0,
        "price": 1.0,
        "fees": 0.0,
        "currency": "USD",
        "transaction_date": "2026-05-01"
    }
    response = client.post("/portfolio-transactions", json=deposit_payload)
    assert response.status_code == 201

    # Check cash balance
    response = client.get(f"/portfolio-cash-balances?portfolio_id={portfolio_id}")
    balances = response.json()
    assert Decimal(balances[0]["amount"]) == Decimal("10000.0")

    # Sell
    # To sell, we first need a holding, let's create a buy first (which drops cash by 1505)
    buy_payload = {
        "portfolio_id": portfolio_id,
        "ticker": "AAPL",
        "transaction_type": "buy",
        "quantity": 10.0,
        "price": 150.0,
        "fees": 5.0,
        "currency": "USD",
        "transaction_date": "2026-05-02"
    }
    client.post("/portfolio-transactions", json=buy_payload)

    # Cash should be 10000 - 1505 = 8495
    response = client.get(f"/portfolio-cash-balances?portfolio_id={portfolio_id}")
    assert Decimal(response.json()[0]["amount"]) == Decimal("8495.0")

    # Now sell 5 shares @ 160, 5 fees => proceeds = 800 - 5 = 795
    sell_payload = {
        "portfolio_id": portfolio_id,
        "ticker": "AAPL",
        "transaction_type": "sell",
        "quantity": 5.0,
        "price": 160.0,
        "fees": 5.0,
        "currency": "USD",
        "transaction_date": "2026-05-03"
    }
    response = client.post("/portfolio-transactions", json=sell_payload)
    assert response.status_code == 201

    # Cash should be 8495 + 795 = 9290
    response = client.get(f"/portfolio-cash-balances?portfolio_id={portfolio_id}")
    assert Decimal(response.json()[0]["amount"]) == Decimal("9290.0")
