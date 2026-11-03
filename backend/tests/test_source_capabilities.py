from collections.abc import Generator
from contextlib import contextmanager
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.core.config import Settings
from app.services.source_capability import list_source_capabilities


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


def test_source_capabilities_returns_india_defaults_without_mocking_availability() -> None:
    with _client_with_db() as (client, _db):
        response = client.get("/api/source-capabilities?market=IN")

        assert response.status_code == 200
        body = response.json()
        capabilities = body["data"]
        assert body["meta"]["source"] == "internal"
        assert {item["market"] for item in capabilities} == {"IN"}

        by_capability = {item["capability"]: item for item in capabilities}
        assert by_capability["corporate_announcements"]["status"] == "manual_only"
        assert by_capability["financial_statements"]["status"] == "manual_only"
        assert by_capability["damodaran_benchmarks"]["status"] == "available"
        assert by_capability["macro_sensitivity"]["status"] == "available"
        assert by_capability["market_prices"]["status"] == "not_configured"
        assert by_capability["market_prices"]["requires_api_key"] is True


def test_source_capabilities_filters_us_features() -> None:
    with _client_with_db() as (client, _db):
        response = client.get("/api/source-capabilities?market=US")

        assert response.status_code == 200
        capabilities = response.json()["data"]
        assert {item["market"] for item in capabilities} == {"US"}

        by_capability = {item["capability"]: item for item in capabilities}
        assert by_capability["sec_filings"]["source_type"] == "filings"
        assert by_capability["sec_fundamentals"]["source_type"] == "fundamentals"
        assert by_capability["market_prices"]["status"] == "not_configured"


def test_source_capabilities_rejects_unsupported_market() -> None:
    with _client_with_db() as (client, _db):
        response = client.get("/api/source-capabilities?market=UK")

        assert response.status_code == 400
        assert response.json()["detail"] == "Unsupported market. Use US or IN."


@pytest.mark.parametrize("provider,alpha_key,fmp_key,expected_status,expected_name,needs_key", [
    ("alphavantage", None, "unused-fixture-key", "not_configured", "Alpha Vantage", True),
    ("alpha_vantage", "fixture-key", None, "available", "Alpha Vantage", True),
    ("yfinance_personal", None, None, "available", "yfinance personal-use", False),
    ("fmp", None, "fixture-key", "not_supported", "FMP", True),
    ("unknown", "fixture-key", "fixture-key", "not_supported", "Unsupported provider", False),
])
def test_prices_describe_only_the_selected_implemented_adapter(provider, alpha_key, fmp_key,
        expected_status, expected_name, needs_key):
    with _client_with_db() as (_client, db):
        settings = Settings(_env_file=None, market_data_provider=provider,
                            alpha_vantage_api_key=alpha_key, fmp_api_key=fmp_key)
        rows = list_source_capabilities(db, settings)
        prices = [row for row in rows if row.capability == "market_prices"]
        assert len(prices) == 2
        for row in prices:
            assert (row.status, row.provider_name, row.requires_api_key) == (
                expected_status, expected_name, needs_key)
            assert "coverage" in row.notes.lower()


def test_fred_and_sec_configuration_is_not_a_claim_of_live_coverage():
    with _client_with_db() as (_client, db):
        missing = Settings(_env_file=None, sec_user_agent="Fixture contact@example.com", fred_api_key=None)
        rows = {row.capability: row for row in list_source_capabilities(db, missing, "US")}
        assert rows["sec_filings"].status == "not_configured"
        assert rows["sec_fundamentals"].status == "not_configured"
        assert rows["fred_macro"].status == "not_configured"
        configured = Settings(_env_file=None, sec_user_agent="Fixture tests@example.invalid", fred_api_key="fixture-key")
        rows = {row.capability: row for row in list_source_capabilities(db, configured, "US")}
        assert rows["fred_macro"].status == "available"
        assert rows["sec_filings"].status == "available"
        assert "coverage" in rows["fred_macro"].notes.lower()


def test_new_default_capabilities_are_added_once_to_existing_catalog():
    from app.models.market_source import MarketSourceCapability
    from sqlalchemy import select
    with _client_with_db() as (_client, db):
        db.add(MarketSourceCapability(market="IN", source_type="filings", provider_name="NSE/BSE",
            capability="corporate_announcements", status="manual_only", notes="Retain this local note"))
        db.commit()
        settings = Settings(_env_file=None)
        first = list_source_capabilities(db, settings)
        second = list_source_capabilities(db, settings)
        assert [row.id for row in first] == [row.id for row in second]
        assert any(row.capability == "fred_macro" for row in first)
        stored = db.scalar(select(MarketSourceCapability).where(MarketSourceCapability.capability == "corporate_announcements"))
        assert stored.notes == "Retain this local note"
