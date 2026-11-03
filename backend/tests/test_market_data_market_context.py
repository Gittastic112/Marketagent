from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Company
from app.models.market_price import CompanyMarketData
from app.services.market_data.base import MarketHistoryResult, MarketQuoteResult


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


def test_market_quote_query_uses_market_exchange_and_ticker() -> None:
    with _client_with_db() as (client, db):
        company = Company(
            ticker="ABC",
            name="ABC India",
            market="IN",
            primary_exchange="NSE",
            local_symbol="ABC",
            currency="INR",
        )
        db.add(company)
        db.flush()
        db.add(
            CompanyMarketData(
                company_id=company.id,
                current_price=Decimal("123.45"),
                currency="INR",
                change_percent=Decimal("1.25"),
                volume=1000,
                last_updated=datetime(2026, 6, 17, tzinfo=timezone.utc),
            )
        )
        db.commit()

        response = client.get("/api/market/quote?market=IN&exchange=NSE&ticker=ABC")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["market"] == "IN"
    assert data["exchange"] == "NSE"
    assert data["ticker"] == "ABC"
    assert data["currency"] == "INR"
    assert data["current_price"] == 123.45


def test_legacy_market_quote_rejects_ambiguous_ticker() -> None:
    with _client_with_db() as (client, db):
        db.add_all(
            [
                Company(ticker="ABC", name="ABC US", market="US", primary_exchange="NASDAQ", local_symbol="ABC"),
                Company(ticker="ABC", name="ABC India", market="IN", primary_exchange="NSE", local_symbol="ABC"),
            ]
        )
        db.commit()

        response = client.get("/api/market/quote/ABC")

    assert response.status_code == 409
    assert response.json()["detail"] == "Ticker is ambiguous across markets. Use market and exchange."


def test_market_ingest_passes_market_context_to_provider(monkeypatch) -> None:
    captured_requests = []

    class FakeProvider:
        provider_name = "fake"

        async def get_quote(self, request):
            captured_requests.append(request)
            return MarketQuoteResult(
                provider_name=self.provider_name,
                provider_symbol=request.ticker,
                market=request.market,
                exchange=request.exchange,
                ticker=request.ticker,
                current_price=Decimal("99.50"),
                change_percent=Decimal("0.75"),
                volume=500,
                currency="INR",
                source_timestamp=datetime(2026, 6, 17, tzinfo=timezone.utc),
                observed_at=datetime(2026, 6, 17, 0, 1, tzinfo=timezone.utc),
                price_type="end_of_day",
            )

        async def get_historical_prices(self, request, days: int = 365):
            captured_requests.append(request)
            return [
                MarketHistoryResult(
                    provider_name=self.provider_name,
                    provider_symbol=request.ticker,
                    market=request.market,
                    exchange=request.exchange,
                    ticker=request.ticker,
                    currency="INR",
                    date="2026-06-17",
                    close_price=Decimal("99.50"),
                    observed_at=datetime(2026, 6, 17, 0, 1, tzinfo=timezone.utc),
                    adjustment_state="unadjusted",
                )
            ]

    monkeypatch.setattr("app.services.market_data.ingestion.get_market_data_provider", lambda: FakeProvider())

    with _client_with_db() as (client, db):
        db.add(
            Company(
                ticker="ABC",
                name="ABC India",
                market="IN",
                primary_exchange="NSE",
                local_symbol="ABC",
                currency="INR",
            )
        )
        db.commit()

        response = client.post(
            "/api/market/ingest",
            json={"market": "IN", "exchange": "NSE", "ticker": "ABC"},
        )

    assert response.status_code == 200
    assert response.json()["data"]["fetched_count"] == 2
    assert len(captured_requests) == 2
    assert captured_requests[0].market == "IN"
    assert captured_requests[0].exchange == "NSE"
    assert captured_requests[0].ticker == "ABC"
    assert captured_requests[0].currency == "INR"


def test_market_quote_response_exposes_persisted_provider_provenance() -> None:
    with _client_with_db() as (client, db):
        company = Company(
            ticker="ABC",
            name="ABC India",
            market="IN",
            primary_exchange="NSE",
            local_symbol="ABC",
            currency="INR",
        )
        db.add(company)
        db.flush()
        db.add(
            CompanyMarketData(
                company_id=company.id,
                current_price=Decimal("123.45"),
                currency="INR",
                provider_name="fixture_provider",
                provider_symbol="ABC.TEST",
                price_type="delayed",
                delay_minutes=15,
                adjustment_state="not_applicable",
                warnings_json=["Fixture quote"],
                source_timestamp=datetime(2026, 6, 17, tzinfo=timezone.utc),
                observed_at=datetime(2026, 6, 17, 0, 1, tzinfo=timezone.utc),
                last_updated=datetime(2026, 6, 17, 0, 1, tzinfo=timezone.utc),
            )
        )
        db.commit()

        response = client.get("/api/market/quote?market=IN&exchange=NSE&ticker=ABC")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["provider_name"] == "fixture_provider"
    assert data["provider_symbol"] == "ABC.TEST"
    assert data["price_type"] == "delayed"
    assert data["delay_minutes"] == 15
    assert data["warnings"] == ["Fixture quote"]
