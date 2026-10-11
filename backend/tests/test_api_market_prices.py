from collections.abc import Generator
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Company, MarketPrice
from app.models.market_price import CompanyMarketData
from app.models.processing_run import ProcessingRun
from app.services.market_data.base import MarketDataProviderError, MarketQuoteResult
from helpers import response_data

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
    data = response_data(response)
    assert data["ticker"] == "TEST"
    assert data["price"] == 150.25
    assert data["currency"] == "USD"
    assert data["as_of_date"] == "2026-05-28"
    assert data["company_id"] == company.id
    assert data["provider_name"] == "manual"
    assert data["price_type"] == "manual"
    assert data["adjustment_state"] == "not_applicable"
    assert data["warnings"] == []

    # Verify db
    price = db.query(MarketPrice).filter_by(id=data["id"]).first()
    assert price is not None
    assert float(price.price) == 150.25


def test_create_market_price_triggers_divergence_check_on_write(
    client: TestClient,
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    company = Company(ticker="WRITE", name="Write Trigger", active=True)
    db.add(company)
    db.commit()
    checked_company_ids: list[int | None] = []
    monkeypatch.setattr(
        "app.api.routers.market_prices.check_price_valuation_divergence",
        lambda session, company_id, **kwargs: checked_company_ids.append(company_id),
    )

    response = client.post("/market-prices", json={
        "company_id": company.id,
        "ticker": company.ticker,
        "price": 10,
        "currency": "USD",
        "as_of_date": "2026-08-22",
    })

    assert response.status_code == 201, response.text
    assert checked_company_ids == [company.id]


def test_list_market_prices(client: TestClient, db: Session) -> None:
    p1 = MarketPrice(ticker="AAPL", price=100.0, currency="USD", as_of_date=date(2026, 5, 27))
    p2 = MarketPrice(ticker="AAPL", price=105.0, currency="USD", as_of_date=date(2026, 5, 28))
    p3 = MarketPrice(ticker="MSFT", price=200.0, currency="USD", as_of_date=date(2026, 5, 28))
    db.add_all([p1, p2, p3])
    db.commit()

    # List all
    response = client.get("/market-prices")
    assert response.status_code == 200
    data = response_data(response)
    assert len(data) >= 3

    # Filter by ticker
    response = client.get("/market-prices?ticker=AAPL")
    assert response.status_code == 200
    data = response_data(response)
    assert len(data) == 2
    assert data[0]["ticker"] == "AAPL"


def test_get_market_price(client: TestClient, db: Session) -> None:
    p1 = MarketPrice(ticker="AAPL", price=100.0, currency="USD", as_of_date=date(2026, 5, 27))
    db.add(p1)
    db.commit()

    response = client.get(f"/market-prices/{p1.id}")
    assert response.status_code == 200
    data = response_data(response)
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
    data = response_data(response)
    assert data["price"] == 102.5


def test_delete_market_price(client: TestClient, db: Session) -> None:
    p1 = MarketPrice(ticker="AAPL", price=100.0, currency="USD", as_of_date=date(2026, 5, 27))
    db.add(p1)
    db.commit()

    response = client.delete(f"/market-prices/{p1.id}")
    assert response.status_code == 204

    assert db.query(MarketPrice).filter_by(id=p1.id).first() is None


def test_fetch_latest_uses_configured_provider_and_persists_provenance(
    client: TestClient,
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    company = Company(
        ticker="ADANIPORTS",
        local_symbol="ADANIPORTS",
        name="Adani Ports",
        market="IN",
        primary_exchange="NSE",
        currency="INR",
        active=True,
    )
    db.add(company)
    db.commit()

    captured = []

    class FakeProvider:
        provider_name = "fixture_provider"

        async def get_quote(self, request):
            captured.append(request)
            return MarketQuoteResult(
                provider_name=self.provider_name,
                provider_symbol="ADANIPORTS.TEST",
                market=request.market,
                exchange=request.exchange,
                ticker=request.ticker,
                currency="INR",
                current_price=Decimal("1234.50"),
                source_timestamp=datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc),
                observed_at=datetime(2026, 8, 1, 10, 1, tzinfo=timezone.utc),
                price_type="delayed",
                delay_minutes=15,
                adjustment_state="not_applicable",
                warnings=["Fixture quote"],
            )

    monkeypatch.setattr(
        "app.services.market_data.ingestion.get_market_data_provider",
        lambda: FakeProvider(),
    )

    response = client.post(f"/market-prices/fetch-latest?company_id={company.id}")

    assert response.status_code == 201
    data = response_data(response)
    assert data["ticker"] == "ADANIPORTS"
    assert data["provider_symbol"] == "ADANIPORTS.TEST"
    assert data["provider_name"] == "fixture_provider"
    assert data["market"] == "IN"
    assert data["exchange"] == "NSE"
    assert data["currency"] == "INR"
    assert data["price"] == 1234.5
    assert data["price_type"] == "delayed"
    assert data["delay_minutes"] == 15
    assert data["warnings"] == ["Fixture quote"]
    assert captured[0].ticker == "ADANIPORTS"

    persisted = db.get(MarketPrice, data["id"])
    assert persisted is not None
    assert persisted.provider_name == "fixture_provider"
    current = db.query(CompanyMarketData).filter_by(company_id=company.id).one()
    assert current.provider_name == "fixture_provider"
    first_run = db.query(ProcessingRun).order_by(ProcessingRun.id.desc()).first()
    assert first_run is not None
    assert first_run.created_count == 1
    assert first_run.skipped_duplicate_count == 0

    repeated_response = client.post(f"/market-prices/fetch-latest?company_id={company.id}")

    assert repeated_response.status_code == 201
    assert response_data(repeated_response)["id"] == data["id"]
    repeated_run = db.query(ProcessingRun).order_by(ProcessingRun.id.desc()).first()
    assert repeated_run is not None
    assert repeated_run.created_count == 0
    assert repeated_run.skipped_duplicate_count == 1


def test_fetch_latest_preserves_provider_error_code(
    client: TestClient,
    db: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    company = Company(ticker="AAPL", name="Apple", market="US", currency="USD", active=True)
    db.add(company)
    db.commit()

    class MissingProvider:
        provider_name = "missing_provider"

        async def get_quote(self, request):
            raise MarketDataProviderError(
                code="PROVIDER_NOT_CONFIGURED",
                message="The selected market data provider is not configured.",
                provider=self.provider_name,
                status_code=503,
                retryable=False,
            )

    monkeypatch.setattr(
        "app.services.market_data.ingestion.get_market_data_provider",
        lambda: MissingProvider(),
    )

    response = client.post(f"/market-prices/fetch-latest?company_id={company.id}")

    assert response.status_code == 503
    error = response.json()["errors"][0]
    assert error["code"] == "PROVIDER_NOT_CONFIGURED"
    assert error["message"] == "The selected market data provider is not configured."
    assert error["retryable"] is False
    assert error["provider"] == "missing_provider"
    assert error["processing_run_id"] is not None
