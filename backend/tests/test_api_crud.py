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


def test_create_list_and_get_company(client: TestClient) -> None:
    response = client.post(
        "/companies",
        json={
            "ticker": "AAPL",
            "name": "Apple Inc.",
            "sector": "Technology",
            "aliases_json": ["Apple"],
            "country": "United States",
            "region": "North America",
            "currency": "USD",
            "asset_type": "equity",
            "security_type": "common_stock",
            "market_cap_category": "mega_cap",
            "is_etf": False,
            "etf_provider": None,
        },
    )

    assert response.status_code == 201
    created = response.json()
    assert created["ticker"] == "AAPL"
    assert created["active"] is True
    assert created["aliases_json"] == ["Apple"]
    assert created["country"] == "United States"
    assert created["currency"] == "USD"
    assert created["asset_type"] == "equity"
    assert created["is_etf"] is False

    list_response = client.get("/companies")
    get_response = client.get(f"/companies/{created['id']}")

    assert list_response.json()[0]["ticker"] == "AAPL"
    assert get_response.json()["name"] == "Apple Inc."
    assert get_response.json()["aliases_json"] == ["Apple"]
    assert get_response.json()["market_cap_category"] == "mega_cap"


def test_create_list_and_get_source(client: TestClient) -> None:
    response = client.post(
        "/sources",
        json={"name": "SEC EDGAR", "source_type": "filing", "reliability_score": 95},
    )

    assert response.status_code == 201
    created = response.json()
    assert created["name"] == "SEC EDGAR"
    assert created["active"] is True

    assert client.get("/sources").json()[0]["source_type"] == "filing"
    assert client.get(f"/sources/{created['id']}").json()["reliability_score"] == 95

    update_response = client.patch(f"/sources/{created['id']}", json={"active": False})
    assert update_response.status_code == 200
    assert update_response.json()["active"] is False


def test_create_list_and_get_raw_document(client: TestClient) -> None:
    company = client.post("/companies", json={"ticker": "MSFT", "name": "Microsoft"}).json()
    source = client.post("/sources", json={"name": "Manual", "source_type": "manual"}).json()

    response = client.post(
        "/raw-documents",
        json={
            "company_id": company["id"],
            "source_id": source["id"],
            "document_type": "manual_note",
            "title": "Manual research note",
            "raw_text": "Cloud margin note",
            "raw_payload_json": {"origin": "manual"},
            "content_hash": "manual-hash-1",
        },
    )

    assert response.status_code == 201
    created = response.json()
    assert created["title"] == "Manual research note"

    assert client.get("/raw-documents").json()[0]["content_hash"] == "manual-hash-1"
    assert client.get(f"/raw-documents/{created['id']}").json()["source_id"] == source["id"]


def test_create_list_and_get_event(client: TestClient) -> None:
    company = client.post("/companies", json={"ticker": "NVDA", "name": "NVIDIA"}).json()

    response = client.post(
        "/events",
        json={
            "company_id": company["id"],
            "event_type": "manual_event",
            "information_speed": "medium",
            "title": "Manual event",
            "description": "A manually entered event.",
            "credibility_score": 70,
            "novelty_score": 60,
            "impact_score": 65,
            "priority_score": 66,
        },
    )

    assert response.status_code == 201
    created = response.json()
    assert created["information_speed"] == "medium"

    assert client.get("/events").json()[0]["title"] == "Manual event"
    assert client.get(f"/events/{created['id']}").json()["company_id"] == company["id"]


def test_create_list_and_get_alert(client: TestClient) -> None:
    company = client.post("/companies", json={"ticker": "TSLA", "name": "Tesla"}).json()
    event = client.post(
        "/events",
        json={
            "company_id": company["id"],
            "event_type": "manual_event",
            "information_speed": "medium",
            "title": "Guidance changed",
        },
    ).json()

    response = client.post(
        "/alerts",
        json={
            "company_id": company["id"],
            "event_id": event["id"],
            "alert_type": "manual_alert",
            "severity": "medium",
            "title": "Review guidance",
            "summary": "Guidance may have changed.",
            "confidence_bucket": "medium",
        },
    )

    assert response.status_code == 201
    created = response.json()
    assert created["review_status"] == "unreviewed"

    assert client.get("/alerts").json()[0]["title"] == "Review guidance"
    assert client.get(f"/alerts/{created['id']}").json()["event_id"] == event["id"]


def test_create_list_and_get_thesis_note(client: TestClient) -> None:
    company = client.post("/companies", json={"ticker": "AMZN", "name": "Amazon"}).json()

    response = client.post(
        "/thesis-notes",
        json={
            "company_id": company["id"],
            "title": "AWS thesis",
            "thesis_text": "AWS growth remains central.",
            "assumptions_json": {"aws_growth": "durable"},
        },
    )

    assert response.status_code == 201
    created = response.json()
    assert created["status"] == "active"

    assert client.get("/thesis-notes").json()[0]["title"] == "AWS thesis"
    assert client.get(f"/thesis-notes/{created['id']}").json()["company_id"] == company["id"]
