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


def test_us_company_lookup_routes_to_sec_provider(monkeypatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}}

    def fake_get(url: str, **kwargs: object) -> FakeResponse:
        assert url == "https://www.sec.gov/files/company_tickers.json"
        return FakeResponse()

    monkeypatch.setattr("app.services.sec_ingestion.httpx.get", fake_get)

    with _client_with_db() as (client, _db):
        response = client.get("/companies/lookup?market=US&ticker=AAPL")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["market"] == "US"
    assert data["ticker"] == "AAPL"
    assert data["local_symbol"] == "AAPL"
    assert data["name"] == "Apple Inc."
    assert data["currency"] == "USD"
    assert data["country"] == "United States"
    assert data["regulatory_id"] == "0000320193"
    assert data["regulatory_id_type"] == "CIK"
    assert data["cik"] == "0000320193"
    assert data["source"] == "SEC EDGAR"


def test_india_company_lookup_returns_existing_local_company() -> None:
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
                isin="INE002A01018",
            )
        )
        db.commit()

        response = client.get("/companies/lookup?market=IN&exchange=NSE&ticker=RELIANCE")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["market"] == "IN"
    assert data["primary_exchange"] == "NSE"
    assert data["local_symbol"] == "RELIANCE"
    assert data["currency"] == "INR"
    assert data["country"] == "India"
    assert data["isin"] == "INE002A01018"
    assert data["source"] == "local_company"


def test_india_company_lookup_is_honest_when_provider_missing() -> None:
    with _client_with_db() as (client, _db):
        response = client.get("/companies/lookup?market=IN&exchange=NSE&ticker=RELIANCE")

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "India company lookup provider not implemented; add company manually or configure provider"
    )


def test_company_lookup_rejects_unsupported_market() -> None:
    with _client_with_db() as (client, _db):
        response = client.get("/companies/lookup?market=UK&ticker=VOD")

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported market UK"
