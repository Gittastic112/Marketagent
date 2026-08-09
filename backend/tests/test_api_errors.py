from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from helpers import response_data


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
    assert response.json()["detail"] == "Company identity US/-/AAPL already exists"


def test_duplicate_source_name_returns_conflict(client: TestClient) -> None:
    client.post("/sources", json={"name": "SEC EDGAR", "source_type": "filing"})

    response = client.post("/sources", json={"name": "SEC EDGAR", "source_type": "filing"})

    assert response.status_code == 409
    assert response.json()["detail"] == "Record already exists"


def test_duplicate_raw_document_hash_returns_conflict(client: TestClient) -> None:
    source_response = client.post("/sources", json={"name": "Manual", "source_type": "manual"})
    assert source_response.status_code == 201
    source = response_data(source_response)
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


def test_delete_company_with_linked_records_returns_clear_conflict(client: TestClient) -> None:
    company_response = client.post("/companies", json={"ticker": "AAPL", "name": "Apple Inc."})
    source_response = client.post("/sources", json={"name": "SEC EDGAR", "source_type": "sec"})
    assert company_response.status_code == 201
    assert source_response.status_code == 201
    company = response_data(company_response)
    source = response_data(source_response)
    client.post(
        "/raw-documents",
        json={
            "company_id": company["id"],
            "source_id": source["id"],
            "document_type": "sec_filing_metadata",
            "title": "Apple 10-K",
            "content_hash": "delete-company-linked-document",
        },
    )

    response = client.delete(f"/companies/{company['id']}")

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Company cannot be deleted while it has linked records. "
        "Delete linked documents, events, alerts, and thesis notes first, or mark the company inactive."
    )


def test_delete_source_with_linked_documents_returns_clear_conflict(client: TestClient) -> None:
    source_response = client.post("/sources", json={"name": "Manual", "source_type": "manual"})
    assert source_response.status_code == 201
    source = response_data(source_response)
    client.post(
        "/raw-documents",
        json={
            "source_id": source["id"],
            "document_type": "manual_note",
            "title": "Manual note",
            "content_hash": "delete-source-linked-document",
        },
    )

    response = client.delete(f"/sources/{source['id']}")

    assert response.status_code == 409
    assert response.json()["detail"] == "Source cannot be deleted while it has linked raw documents. Delete linked documents first or mark the source inactive."


def test_delete_raw_document_with_linked_events_returns_clear_conflict(client: TestClient) -> None:
    source_response = client.post("/sources", json={"name": "Manual", "source_type": "manual"})
    assert source_response.status_code == 201
    source = response_data(source_response)
    document_response = client.post(
        "/raw-documents",
        json={
            "source_id": source["id"],
            "document_type": "manual_note",
            "title": "Manual note",
            "content_hash": "delete-document-linked-event",
        },
    )
    assert document_response.status_code == 201
    document = response_data(document_response)
    client.post(
        "/events",
        json={
            "raw_document_id": document["id"],
            "event_type": "manual_event",
            "information_speed": "medium",
            "title": "Linked event",
        },
    )

    response = client.delete(f"/raw-documents/{document['id']}")

    assert response.status_code == 409
    assert response.json()["detail"] == "Raw document cannot be deleted while it has linked events. Delete linked events first."


def test_delete_event_with_linked_alerts_returns_clear_conflict(client: TestClient) -> None:
    event_response = client.post(
        "/events",
        json={
            "event_type": "manual_event",
            "information_speed": "medium",
            "title": "Linked event",
        },
    )
    assert event_response.status_code == 201
    event = response_data(event_response)
    client.post(
        "/alerts",
        json={
            "event_id": event["id"],
            "alert_type": "manual_alert",
            "title": "Linked alert",
        },
    )

    response = client.delete(f"/events/{event['id']}")

    assert response.status_code == 409
    assert response.json()["detail"] == "Event cannot be deleted while it has linked alerts. Delete linked alerts first."
