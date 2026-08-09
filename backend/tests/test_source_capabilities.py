from collections.abc import Generator
from contextlib import contextmanager

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
