from collections.abc import Generator
from contextlib import contextmanager

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Company


@contextmanager
def _client_with_db() -> Generator[tuple[TestClient, Session]]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)
    db = TestingSessionLocal()

    def override_get_db() -> Generator[Session]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client, db
    finally:
        app.dependency_overrides.clear()
        db.close()


def test_india_company_valuation_context_defaults_to_inr_and_india_benchmarks() -> None:
    with _client_with_db() as (client, db):
        db.add(
            Company(
                ticker="RELIANCE",
                name="Reliance Industries",
                market="IN",
                primary_exchange="NSE",
                local_symbol="RELIANCE",
                country="India",
                currency="INR",
            )
        )
        db.commit()

        response = client.get("/api/valuation/context/company/1")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["company_id"] == 1
    assert data["market"] == "IN"
    assert data["country"] == "India"
    assert data["default_currency"] == "INR"
    assert data["recommended_benchmark_country"] == "India"
    assert "India" in data["available_benchmark_countries"]
    assert "Cash flows and discount rate must be in the same currency." in data["warnings"]


def test_us_company_valuation_context_defaults_to_usd_and_us_benchmarks() -> None:
    with _client_with_db() as (client, db):
        db.add(
            Company(
                ticker="AAPL",
                name="Apple Inc.",
                market="US",
                primary_exchange="NASDAQ",
                local_symbol="AAPL",
                country="United States",
                currency="USD",
            )
        )
        db.commit()

        response = client.get("/api/valuation/context/company/1")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["market"] == "US"
    assert data["country"] == "United States"
    assert data["default_currency"] == "USD"
    assert data["recommended_benchmark_country"] == "United States"


def test_valuation_context_requires_existing_company() -> None:
    with _client_with_db() as (client, _db):
        response = client.get("/api/valuation/context/company/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Company not found"
