from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Alert, Company, ProcessingRun, Source, ThesisNote
from helpers import response_data


def unwrap(response):
    return response_data(response)


@pytest.fixture
def client() -> Generator[TestClient]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    with TestingSessionLocal() as db:
        company = Company(ticker="MSFT", name="Microsoft", cik="0000789019")
        db.add_all([
            company,
            Source(name="SEC EDGAR", source_type="sec", reliability_score=95),
            ThesisNote(company=company, title="Cloud thesis", thesis_text="Cloud demand remains important."),
        ])
        db.commit()

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


def test_post_sec_ingestion_imports_supplied_metadata(client: TestClient) -> None:
    response = client.post(
        "/ingest/sec-filings",
        json={
            "source_id": 1,
            "company_id": 1,
            "filings": [
                {
                    "accession_number": "0000789019-26-000123",
                    "form_type": "10-Q",
                    "filing_date": "2026-05-24",
                    "report_date": "2026-03-31",
                    "primary_document": "msft-20260331.htm",
                    "filing_url": "https://www.sec.gov/example/msft-20260331.htm",
                }
            ],
        },
    )

    assert response.status_code == 201
    body = response_data(response)
    assert body["fetched_count"] == 1
    assert body["created_count"] == 1
    assert body["skipped_duplicate_count"] == 0
    assert body["error_count"] == 0
    assert body["created"] == 1
    assert body["skipped_duplicates"] == 0
    assert body["events_created"] == 1
    assert body["events_skipped_existing"] == 0
    assert body["alerts_created"] == 1
    assert body["alerts_skipped_existing"] == 0

    documents = response_data(client.get("/raw-documents"))
    events = response_data(client.get("/events"))
    alerts = response_data(client.get("/alerts"))

    assert documents[0]["document_type"] == "sec_filing_metadata"
    assert documents[0]["raw_payload_json"]["accession_number"] == "0000789019-26-000123"
    assert events[0]["event_type"] == "sec_filing"
    assert events[0]["priority_score"] >= 70
    assert alerts[0]["title"] == "Review: MSFT 10-Q filed 2026-05-24"
    with next(app.dependency_overrides[get_db]()) as db:
        alert = db.query(Alert).one()
    assert alert.user_id == "admin_user_id_fallback"


def test_post_sec_ingestion_resolves_or_creates_default_source(client: TestClient) -> None:
    with next(app.dependency_overrides[get_db]()) as db:
        source = db.query(Source).filter(Source.name == "SEC EDGAR").one()
        db.delete(source)
        db.commit()

    response = client.post(
        "/ingest/sec-filings",
        json={
            "company_id": 1,
            "filings": [
                {
                    "accession_number": "0000789019-26-000124",
                    "form_type": "10-Q",
                    "filing_date": "2026-05-25",
                    "filing_url": "https://www.sec.gov/example/msft-20260525.htm",
                }
            ],
        },
    )

    assert response.status_code == 201
    assert response_data(response)["created_count"] == 1
    sources = response_data(client.get("/sources"))
    assert len(sources) == 1
    assert sources[0]["name"] == "SEC EDGAR"
    assert sources[0]["source_type"] == "sec"
    documents = response_data(client.get("/raw-documents"))
    assert documents[0]["source_id"] == sources[0]["id"]


def test_post_sec_ingestion_can_download_filing_text(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        text = "<html><body>Downloaded SEC filing text</body></html>"

        def raise_for_status(self) -> None:
            return None

    def fake_get(url: str, **kwargs: object) -> FakeResponse:
        assert url == "https://www.sec.gov/example/msft-20260331.htm"
        return FakeResponse()

    monkeypatch.setattr("app.providers.sec_provider.fetch_public_text", lambda url, **kwargs: fake_get(url, **kwargs).text)

    response = client.post(
        "/ingest/sec-filings",
        json={
            "source_id": 1,
            "company_id": 1,
            "download_text": True,
            "filings": [
                {
                    "accession_number": "0000789019-26-000123",
                    "form_type": "10-Q",
                    "filing_date": "2026-05-24",
                    "report_date": "2026-03-31",
                    "primary_document": "msft-20260331.htm",
                    "filing_url": "https://www.sec.gov/example/msft-20260331.htm",
                }
            ],
        },
    )

    assert response.status_code == 201
    assert response_data(response)["created_count"] == 1

    documents = response_data(client.get("/raw-documents"))
    assert documents[0]["raw_text"] == "<html><body>Downloaded SEC filing text</body></html>"
    assert documents[0]["raw_payload_json"]["text_downloaded"] is True


def test_post_sec_ingestion_persists_processing_run(client: TestClient) -> None:
    response = client.post(
        "/ingest/sec-filings",
        json={
            "source_id": 1,
            "company_id": 1,
            "filings": [
                {
                    "accession_number": "0000789019-26-000123",
                    "form_type": "10-Q",
                    "filing_date": "2026-05-24",
                    "report_date": "2026-03-31",
                    "primary_document": "msft-20260331.htm",
                    "filing_url": "https://www.sec.gov/example/msft-20260331.htm",
                }
            ],
        },
    )

    assert response.status_code == 201

    with next(app.dependency_overrides[get_db]()) as db:
        run = db.query(ProcessingRun).one()

    assert run.run_type == "sec_ingestion"
    assert run.source_type == "sec"
    assert run.source_id == 1
    assert run.company_id == 1
    assert run.status == "success"
    assert run.fetched_count == 1
    assert run.created_count == 1
    assert run.skipped_duplicate_count == 0
    assert run.error_count == 0
    assert run.finished_at is not None


def test_post_sec_ingestion_rejects_missing_company(client: TestClient) -> None:
    response = client.post(
        "/ingest/sec-filings",
        json={
            "source_id": 1,
            "company_id": 999,
            "filings": [],
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Company not found"


def test_post_recent_sec_ingestion_fetches_by_company_cik(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "filings": {
                    "recent": {
                        "accessionNumber": ["0000789019-26-000123"],
                        "form": ["10-Q"],
                        "filingDate": ["2026-05-24"],
                        "reportDate": ["2026-03-31"],
                        "primaryDocument": ["msft-20260331.htm"],
                    }
                }
            }

    def fake_get(url: str, **kwargs: object) -> FakeResponse:
        assert url == "https://data.sec.gov/submissions/CIK0000789019.json"
        return FakeResponse()

    monkeypatch.setattr("app.services.sec_ingestion.fetch_public_json", lambda url, **kwargs: fake_get(url, **kwargs).json())

    response = client.post("/ingest/sec-filings/recent", json={"source_id": 1, "company_id": 1})

    assert response.status_code == 201
    body = response_data(response)
    assert body["fetched_count"] == 1
    assert body["created_count"] == 1
    assert body["error_count"] == 0
    assert body["events_created"] == 1
    assert body["alerts_created"] == 1


def test_get_company_sec_filings_preview_filters_form_and_year(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "filings": {
                    "recent": {
                        "accessionNumber": ["0000789019-26-000123", "0000789019-25-000123"],
                        "form": ["10-K", "10-K"],
                        "filingDate": ["2026-05-24", "2025-05-24"],
                        "reportDate": ["2026-03-31", "2025-03-31"],
                        "primaryDocument": ["msft-2026.htm", "msft-2025.htm"],
                    }
                }
            }

    def fake_get(url: str, **kwargs: object) -> FakeResponse:
        assert url == "https://data.sec.gov/submissions/CIK0000789019.json"
        return FakeResponse()

    monkeypatch.setattr("app.services.sec_ingestion.fetch_public_json", lambda url, **kwargs: fake_get(url, **kwargs).json())

    response = client.get("/companies/1/sec-filings/preview?form_type=10-K&filing_year=2026")

    assert response.status_code == 200
    assert response_data(response) == [
        {
            "accession_number": "0000789019-26-000123",
            "form_type": "10-K",
            "filing_date": "2026-05-24",
            "report_date": "2026-03-31",
            "primary_document": "msft-2026.htm",
            "filing_url": "https://www.sec.gov/Archives/edgar/data/789019/000078901926000123/msft-2026.htm",
        }
    ]


def test_post_company_lookup_cik_updates_company(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"0": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corp."}}

    def fake_get(url: str, **kwargs: object) -> FakeResponse:
        assert url == "https://www.sec.gov/files/company_tickers.json"
        return FakeResponse()

    monkeypatch.setattr("app.services.sec_ingestion.fetch_public_json", lambda url, **kwargs: fake_get(url, **kwargs).json())
    client.patch("/companies/1", json={"cik": None})

    response = client.post("/companies/1/lookup-cik")

    assert response.status_code == 200
    assert unwrap(response)["cik"] == "0000789019"


def test_get_company_lookup_returns_sec_title_and_cik(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}}

    def fake_get(url: str, **kwargs: object) -> FakeResponse:
        assert url == "https://www.sec.gov/files/company_tickers.json"
        return FakeResponse()

    monkeypatch.setattr("app.services.sec_ingestion.fetch_public_json", lambda url, **kwargs: fake_get(url, **kwargs).json())

    response = client.get("/companies/lookup?ticker=AAPL")

    assert response.status_code == 200
    data = unwrap(response)
    assert data["ticker"] == "AAPL"
    assert data["name"] == "Apple Inc."
    assert data["cik"] == "0000320193"
    assert data["market"] == "US"
    assert data["regulatory_id_type"] == "CIK"
