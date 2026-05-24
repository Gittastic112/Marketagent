from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app


@pytest.fixture
def client() -> Generator[TestClient]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

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


def test_duplicate_company_ticker_returns_conflict(client: TestClient) -> None:
    client.post("/companies", json={"ticker": "AAPL", "name": "Apple Inc."})

    response = client.post("/companies", json={"ticker": "AAPL", "name": "Apple Duplicate"})

    assert response.status_code == 409
    assert response.json()["detail"] == "Record already exists"


def test_duplicate_source_name_returns_conflict(client: TestClient) -> None:
    client.post("/sources", json={"name": "SEC EDGAR", "source_type": "filing"})

    response = client.post("/sources", json={"name": "SEC EDGAR", "source_type": "filing"})

    assert response.status_code == 409
    assert response.json()["detail"] == "Record already exists"


def test_duplicate_raw_document_hash_returns_conflict(client: TestClient) -> None:
    source = client.post("/sources", json={"name": "Manual", "source_type": "manual"}).json()
    payload = {
        "source_id": source["id"],
        "document_type": "manual_note",
        "title": "Manual note",
        "content_hash": "same-hash",
    }
    client.post("/raw-documents", json=payload)

    response = client.post("/raw-documents", json=payload)

    assert response.status_code == 409
    assert response.json()["detail"] == "Record already exists"


def test_raw_document_requires_existing_source(client: TestClient) -> None:
    response = client.post(
        "/raw-documents",
        json={
            "source_id": 999,
            "document_type": "manual_note",
            "title": "Missing source",
            "content_hash": "missing-source-hash",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Source not found"


def test_event_requires_existing_raw_document_when_provided(client: TestClient) -> None:
    response = client.post(
        "/events",
        json={
            "raw_document_id": 999,
            "event_type": "manual_event",
            "information_speed": "medium",
            "title": "Missing document",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Raw document not found"


def test_alert_requires_existing_event_when_provided(client: TestClient) -> None:
    response = client.post(
        "/alerts",
        json={"event_id": 999, "alert_type": "manual_alert", "title": "Missing event"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"


def test_thesis_note_requires_existing_company(client: TestClient) -> None:
    response = client.post(
        "/thesis-notes",
        json={"company_id": 999, "title": "Missing company", "thesis_text": "Text."},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Company not found"
