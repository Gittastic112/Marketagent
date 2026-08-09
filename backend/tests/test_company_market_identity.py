from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app


def unwrap(response: object) -> dict:
    payload = response.json()
    return payload.get("data", payload)


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


def test_companies_can_share_ticker_across_different_markets(client: TestClient) -> None:
    us_response = client.post(
        "/companies",
        json={
            "ticker": "ABC",
            "name": "ABC US",
            "market": "US",
            "primary_exchange": "NASDAQ",
            "local_symbol": "ABC",
        },
    )
    india_response = client.post(
        "/companies",
        json={
            "ticker": "ABC",
            "name": "ABC India",
            "market": "IN",
            "primary_exchange": "NSE",
            "local_symbol": "ABC",
        },
    )

    assert us_response.status_code == 201
    assert india_response.status_code == 201

    us_company = unwrap(us_response)
    india_company = unwrap(india_response)

    assert us_company["ticker"] == "ABC"
    assert us_company["market"] == "US"
    assert us_company["primary_exchange"] == "NASDAQ"
    assert us_company["local_symbol"] == "ABC"
    assert us_company["currency"] == "USD"
    assert us_company["country"] == "United States"

    assert india_company["ticker"] == "ABC"
    assert india_company["market"] == "IN"
    assert india_company["primary_exchange"] == "NSE"
    assert india_company["local_symbol"] == "ABC"
    assert india_company["currency"] == "INR"
    assert india_company["country"] == "India"


def test_duplicate_market_exchange_symbol_is_rejected(client: TestClient) -> None:
    first_response = client.post(
        "/companies",
        json={
            "ticker": "RELIANCE",
            "name": "Reliance Industries",
            "market": "IN",
            "primary_exchange": "NSE",
            "local_symbol": "RELIANCE",
        },
    )
    duplicate_response = client.post(
        "/companies",
        json={
            "ticker": "RELIANCE",
            "name": "Reliance Duplicate",
            "market": "IN",
            "primary_exchange": "NSE",
            "local_symbol": "RELIANCE",
        },
    )

    assert first_response.status_code == 201
    assert duplicate_response.status_code == 409
    assert "already exists" in duplicate_response.json()["detail"]


def test_company_market_defaults_for_legacy_payload(client: TestClient) -> None:
    response = client.post("/companies", json={"ticker": "msft", "name": "Microsoft"})

    assert response.status_code == 201
    company = unwrap(response)
    assert company["ticker"] == "MSFT"
    assert company["market"] == "US"
    assert company["primary_exchange"] is None
    assert company["local_symbol"] == "MSFT"
    assert company["currency"] == "USD"
    assert company["country"] == "United States"


def test_india_defaults_country_currency_and_local_symbol(client: TestClient) -> None:
    response = client.post(
        "/companies",
        json={
            "ticker": "reliance",
            "name": "Reliance Industries",
            "market": "in",
            "primary_exchange": "nse",
        },
    )

    assert response.status_code == 201
    company = unwrap(response)
    assert company["ticker"] == "RELIANCE"
    assert company["market"] == "IN"
    assert company["primary_exchange"] == "NSE"
    assert company["local_symbol"] == "RELIANCE"
    assert company["currency"] == "INR"
    assert company["country"] == "India"
