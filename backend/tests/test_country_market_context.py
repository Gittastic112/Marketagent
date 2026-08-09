from collections.abc import Generator
from contextlib import contextmanager
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app


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


def test_market_context_does_not_fabricate_defaults_without_manual_entry() -> None:
    with _client_with_db() as (client, _db):
        response = client.get("/api/market-context?market=IN")

        assert response.status_code == 200
        body = response.json()
        assert body["data"] is None
        assert body["meta"]["status"] == "error"
        assert body["meta"]["source"] == "manual"
        assert body["meta"]["is_stale"] is True
        assert body["errors"][0]["code"] == "MARKET_CONTEXT_NOT_CONFIGURED"
        assert "manual" in body["errors"][0]["message"].lower()


def test_manual_market_context_can_be_created_and_fetched_by_market() -> None:
    with _client_with_db() as (client, _db):
        payload = {
            "market": "in",
            "country": "India",
            "currency": "inr",
            "risk_free_rate": 0.071,
            "risk_free_rate_source": "Manual RBI 10Y government bond yield",
            "equity_risk_premium": 0.055,
            "country_risk_premium": 0.018,
            "inflation_rate": 0.048,
            "fx_rate_to_usd": 83.4,
            "as_of_date": str(date(2026, 6, 18)),
            "notes": "Entered manually from source review.",
        }

        created = client.post("/api/market-context/manual", json=payload)
        assert created.status_code == 201
        created_data = created.json()["data"]
        assert created_data["market"] == "IN"
        assert created_data["currency"] == "INR"
        assert created_data["is_manual"] is True
        assert created_data["risk_free_rate"] == 0.071
        assert created_data["risk_free_rate_source"] == "Manual RBI 10Y government bond yield"

        fetched = client.get("/api/market-context?market=IN")
        assert fetched.status_code == 200
        body = fetched.json()
        assert body["meta"]["status"] == "success"
        assert body["meta"]["source"] == "manual"
        assert body["data"]["country"] == "India"
        assert body["data"]["currency"] == "INR"
        assert body["data"]["risk_free_rate"] == 0.071


def test_risk_free_rate_lookup_is_currency_specific_and_not_cross_market() -> None:
    with _client_with_db() as (client, _db):
        client.post(
            "/api/market-context/manual",
            json={
                "market": "US",
                "country": "United States",
                "currency": "USD",
                "risk_free_rate": 0.043,
                "risk_free_rate_source": "Manual US Treasury 10Y",
                "as_of_date": "2026-06-18",
            },
        )

        usd_response = client.get("/api/valuation/risk-free-rate?currency=USD")
        assert usd_response.status_code == 200
        usd_body = usd_response.json()
        assert usd_body["meta"]["status"] == "success"
        assert usd_body["data"]["currency"] == "USD"
        assert usd_body["data"]["risk_free_rate"] == 0.043

        inr_response = client.get("/api/valuation/risk-free-rate?currency=INR")
        assert inr_response.status_code == 200
        inr_body = inr_response.json()
        assert inr_body["data"] is None
        assert inr_body["meta"]["status"] == "error"
        assert inr_body["errors"][0]["code"] == "RISK_FREE_RATE_NOT_CONFIGURED"
        assert "INR" in inr_body["errors"][0]["message"]


def test_market_context_rejects_unsupported_market() -> None:
    with _client_with_db() as (client, _db):
        response = client.get("/api/market-context?market=UK")

        assert response.status_code == 400
        assert response.json()["detail"] == "Unsupported market. Use US or IN."
