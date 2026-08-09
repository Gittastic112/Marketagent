from collections.abc import Generator
from contextlib import contextmanager
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Company, RawDocument
from app.services.sec_ingestion import SecFilingMetadata


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


def test_us_auto_filing_preview_routes_to_sec(monkeypatch) -> None:
    def fake_fetch_recent_sec_filing_metadata(cik, form_types=("10-K",), filing_year=None, limit=20):
        assert cik == "0000320193"
        assert form_types == ("10-K",)
        assert limit == 2
        return [
            SecFilingMetadata(
                accession_number="0000320193-26-000001",
                form_type="10-K",
                filing_date=date(2026, 6, 1),
                report_date=date(2026, 3, 31),
                primary_document="aapl-20260331.htm",
                filing_url="https://www.sec.gov/example/aapl-20260331.htm",
            )
        ]

    monkeypatch.setattr(
        "app.providers.filings.sec_edgar.fetch_recent_sec_filing_metadata",
        fake_fetch_recent_sec_filing_metadata,
    )

    with _client_with_db() as (client, db):
        db.add(
            Company(
                ticker="AAPL",
                name="Apple Inc.",
                market="US",
                primary_exchange="NASDAQ",
                local_symbol="AAPL",
                cik="0000320193",
            )
        )
        db.commit()

        response = client.get("/companies/1/filings/preview?source=auto&form_type=10-K&limit=2")

    assert response.status_code == 200
    body = response.json()
    assert body["data"][0]["accession_number"] == "0000320193-26-000001"
    assert body["data"][0]["form_type"] == "10-K"
    assert body["meta"]["source"] == "SEC EDGAR"


def test_india_auto_filing_preview_is_not_configured() -> None:
    with _client_with_db() as (client, db):
        db.add(
            Company(
                ticker="RELIANCE",
                name="Reliance Industries",
                market="IN",
                primary_exchange="NSE",
                local_symbol="RELIANCE",
            )
        )
        db.commit()

        response = client.get("/companies/1/filings/preview?source=auto")

    assert response.status_code == 409
    assert response.json()["detail"] == "India automated filing provider not configured; use manual filing upload/link"


def test_india_manual_filing_creates_traceable_raw_document() -> None:
    with _client_with_db() as (client, db):
        db.add(
            Company(
                ticker="RELIANCE",
                name="Reliance Industries",
                market="IN",
                primary_exchange="NSE",
                local_symbol="RELIANCE",
            )
        )
        db.commit()

        response = client.post(
            "/companies/1/filings/manual",
            json={
                "document_type": "annual_report",
                "title": "Reliance annual report FY2026",
                "url": "https://www.bseindia.com/example/reliance-annual-report.pdf",
                "published_at": "2026-06-01T00:00:00Z",
                "raw_text": "Annual report text excerpt",
            },
        )
        document = db.scalar(select(RawDocument).where(RawDocument.company_id == 1))

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["document_type"] == "annual_report"
    assert data["raw_payload_json"]["source_kind"] == "manual_filing"
    assert data["raw_payload_json"]["market"] == "IN"
    assert data["raw_payload_json"]["filing_system"] == "MANUAL_UPLOAD"
    assert document is not None
    assert document.content_hash.startswith("manual-filing:")


def test_manual_filing_rejects_unknown_document_type() -> None:
    with _client_with_db() as (client, db):
        db.add(Company(ticker="ABC", name="ABC India", market="IN", primary_exchange="NSE", local_symbol="ABC"))
        db.commit()

        response = client.post(
            "/companies/1/filings/manual",
            json={"document_type": "rumor", "title": "Bad filing"},
        )

    assert response.status_code == 422
