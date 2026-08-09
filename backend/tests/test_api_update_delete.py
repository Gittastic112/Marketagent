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


def test_update_and_delete_company(client: TestClient) -> None:
    created_response = client.post("/companies", json={"ticker": "META", "name": "Meta"})
    assert created_response.status_code == 201
    created = response_data(created_response)

    update_response = client.patch(
        f"/companies/{created['id']}",
        json={
            "name": "Meta Platforms",
            "sector": "Communication Services",
            "country": "United States",
            "region": "North America",
            "currency": "USD",
            "asset_type": "equity",
            "security_type": "common_stock",
            "market_cap_category": "mega_cap",
            "is_etf": False,
        },
    )
    delete_response = client.delete(f"/companies/{created['id']}")
    get_response = client.get(f"/companies/{created['id']}")

    assert update_response.status_code == 200
    updated = response_data(update_response)
    assert updated["name"] == "Meta Platforms"
    assert updated["country"] == "United States"
    assert updated["security_type"] == "common_stock"
    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_update_and_delete_source(client: TestClient) -> None:
    created_response = client.post("/sources", json={"name": "Manual", "source_type": "manual"})
    assert created_response.status_code == 201
    created = response_data(created_response)

    update_response = client.patch(
        f"/sources/{created['id']}",
        json={"reliability_score": 80, "base_url": "https://example.com"},
    )
    delete_response = client.delete(f"/sources/{created['id']}")
    get_response = client.get(f"/sources/{created['id']}")

    assert update_response.status_code == 200
    assert response_data(update_response)["reliability_score"] == 80
    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_update_and_delete_raw_document(client: TestClient) -> None:
    source_response = client.post("/sources", json={"name": "Manual", "source_type": "manual"})
    assert source_response.status_code == 201
    source = response_data(source_response)
    created_response = client.post(
        "/raw-documents",
        json={
            "source_id": source["id"],
            "document_type": "manual_note",
            "title": "Initial title",
            "content_hash": "document-hash-1",
        },
    )
    assert created_response.status_code == 201
    created = response_data(created_response)

    update_response = client.patch(
        f"/raw-documents/{created['id']}",
        json={"title": "Updated title", "raw_text": "Updated text"},
    )
    delete_response = client.delete(f"/raw-documents/{created['id']}")
    get_response = client.get(f"/raw-documents/{created['id']}")

    assert update_response.status_code == 200
    assert response_data(update_response)["title"] == "Updated title"
    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_update_and_delete_event(client: TestClient) -> None:
    created_response = client.post(
        "/events",
        json={"event_type": "manual_event", "information_speed": "medium", "title": "Initial event"},
    )
    assert created_response.status_code == 201
    created = response_data(created_response)

    update_response = client.patch(
        f"/events/{created['id']}",
        json={"title": "Updated event", "impact_score": 75},
    )
    delete_response = client.delete(f"/events/{created['id']}")
    get_response = client.get(f"/events/{created['id']}")

    assert update_response.status_code == 200
    assert response_data(update_response)["impact_score"] == 75
    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_update_and_delete_alert(client: TestClient) -> None:
    created_response = client.post(
        "/alerts",
        json={"alert_type": "manual_alert", "title": "Initial alert"},
    )
    assert created_response.status_code == 201
    created = response_data(created_response)

    update_response = client.patch(
        f"/alerts/{created['id']}",
        json={"severity": "high", "review_status": "needs_follow_up"},
    )
    delete_response = client.delete(f"/alerts/{created['id']}")
    get_response = client.get(f"/alerts/{created['id']}")

    assert update_response.status_code == 200
    assert response_data(update_response)["review_status"] == "needs_follow_up"
    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_update_and_delete_thesis_note(client: TestClient) -> None:
    company_response = client.post("/companies", json={"ticker": "NFLX", "name": "Netflix"})
    assert company_response.status_code == 201
    company = response_data(company_response)
    created_response = client.post(
        "/thesis-notes",
        json={
            "company_id": company["id"],
            "title": "Initial thesis",
            "thesis_text": "Initial thesis text.",
        },
    )
    assert created_response.status_code == 201
    created = response_data(created_response)

    update_response = client.patch(
        f"/thesis-notes/{created['id']}",
        json={"status": "revised", "thesis_text": "Updated thesis text."},
    )
    delete_response = client.delete(f"/thesis-notes/{created['id']}")
    get_response = client.get(f"/thesis-notes/{created['id']}")

    assert update_response.status_code == 200
    assert response_data(update_response)["status"] == "revised"
    assert delete_response.status_code == 204
    assert get_response.status_code == 404
