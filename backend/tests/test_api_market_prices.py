from collections.abc import Generator

import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Company, MarketPrice


from sqlalchemy.engine import Engine

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


def test_create_market_price(client: TestClient, db: Session) -> None:
    company = Company(ticker="TEST", name="Test Company", active=True)
    db.add(company)
    db.commit()

    response = client.post(
        "/market-prices",
        json={
            "company_id": company.id,
            "ticker": "TEST",
            "price": 150.25,
            "currency": "usd",
            "as_of_date": "2026-05-28"
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["ticker"] == "TEST"
    assert data["price"] == 150.25
    assert data["currency"] == "USD"
    assert data["as_of_date"] == "2026-05-28"
    assert data["company_id"] == company.id

    # Verify db
    price = db.query(MarketPrice).filter_by(id=data["id"]).first()
    assert price is not None
    assert float(price.price) == 150.25


def test_list_market_prices(client: TestClient, db: Session) -> None:
    p1 = MarketPrice(ticker="AAPL", price=100.0, currency="USD", as_of_date=date(2026, 5, 27))
    p2 = MarketPrice(ticker="AAPL", price=105.0, currency="USD", as_of_date=date(2026, 5, 28))
    p3 = MarketPrice(ticker="MSFT", price=200.0, currency="USD", as_of_date=date(2026, 5, 28))
    db.add_all([p1, p2, p3])
    db.commit()

    # List all
    response = client.get("/market-prices")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3

    # Filter by ticker
    response = client.get("/market-prices?ticker=AAPL")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["ticker"] == "AAPL"


def test_get_market_price(client: TestClient, db: Session) -> None:
    p1 = MarketPrice(ticker="AAPL", price=100.0, currency="USD", as_of_date=date(2026, 5, 27))
    db.add(p1)
    db.commit()

    response = client.get(f"/market-prices/{p1.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "AAPL"


def test_update_market_price(client: TestClient, db: Session) -> None:
    p1 = MarketPrice(ticker="AAPL", price=100.0, currency="USD", as_of_date=date(2026, 5, 27))
    db.add(p1)
    db.commit()

    response = client.patch(
        f"/market-prices/{p1.id}",
        json={"price": 102.5}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["price"] == 102.5


def test_delete_market_price(client: TestClient, db: Session) -> None:
    p1 = MarketPrice(ticker="AAPL", price=100.0, currency="USD", as_of_date=date(2026, 5, 27))
    db.add(p1)
    db.commit()

    response = client.delete(f"/market-prices/{p1.id}")
    assert response.status_code == 204

    assert db.query(MarketPrice).filter_by(id=p1.id).first() is None
