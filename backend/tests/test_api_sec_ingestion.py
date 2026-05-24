from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Company, Source


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
        db.add_all([
            Company(ticker="MSFT", name="Microsoft", cik="0000789019"),
            Source(name="SEC EDGAR", source_type="sec"),
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
    body = response.json()
    assert body["created"] == 1
    assert body["skipped_duplicates"] == 0


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
