from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app


def unwrap(response: object):
    payload = response.json()
    return payload.get("data", payload)


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
    created = unwrap(response)
    assert created["ticker"] == "AAPL"
    assert created["active"] is True
    assert created["aliases_json"] == ["Apple"]
    assert created["country"] == "United States"
    assert created["currency"] == "USD"
    assert created["asset_type"] == "equity"
    assert created["is_etf"] is False

    list_response = client.get("/companies")
    get_response = client.get(f"/companies/{created['id']}")

    assert unwrap(list_response)[0]["ticker"] == "AAPL"
    assert unwrap(get_response)["name"] == "Apple Inc."
    assert unwrap(get_response)["aliases_json"] == ["Apple"]
    assert unwrap(get_response)["market_cap_category"] == "mega_cap"


def test_create_list_and_get_source(client: TestClient) -> None:
    response = client.post(
        "/sources",
        json={"name": "SEC EDGAR", "source_type": "filing", "reliability_score": 95},
    )

    assert response.status_code == 201
    created = unwrap(response)
    assert created["name"] == "SEC EDGAR"
    assert created["active"] is True

    assert unwrap(client.get("/sources"))[0]["source_type"] == "filing"
    assert unwrap(client.get(f"/sources/{created['id']}"))["reliability_score"] == 95

    update_response = client.patch(f"/sources/{created['id']}", json={"active": False})
    assert update_response.status_code == 200
    assert unwrap(update_response)["active"] is False


def test_create_list_and_get_raw_document(client: TestClient) -> None:
    company = unwrap(client.post("/companies", json={"ticker": "MSFT", "name": "Microsoft"}))
    source = unwrap(client.post("/sources", json={"name": "Manual", "source_type": "manual"}))

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
    created = unwrap(response)
    assert created["title"] == "Manual research note"

    assert unwrap(client.get("/raw-documents"))[0]["content_hash"] == "manual-hash-1"
    assert unwrap(client.get(f"/raw-documents/{created['id']}"))["source_id"] == source["id"]
    summary = unwrap(client.get(f"/raw-documents/{created['id']}/summary"))
    summaries = unwrap(client.get("/raw-documents/summaries"))
    assert summary["has_raw_text"] is True
    assert summaries[0]["has_raw_text"] is True
    assert "raw_text" not in summary
    assert "raw_text" not in summaries[0]


def test_create_list_and_get_event(client: TestClient) -> None:
    company = unwrap(client.post("/companies", json={"ticker": "NVDA", "name": "NVIDIA"}))

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
    created = unwrap(response)
    assert created["information_speed"] == "medium"

    assert unwrap(client.get("/events"))[0]["title"] == "Manual event"
    assert unwrap(client.get(f"/events/{created['id']}"))["company_id"] == company["id"]


def test_create_list_and_get_alert(client: TestClient) -> None:
    company = unwrap(client.post("/companies", json={"ticker": "TSLA", "name": "Tesla"}))
    event = unwrap(
        client.post(
            "/events",
            json={
                "company_id": company["id"],
                "event_type": "manual_event",
                "information_speed": "medium",
                "title": "Guidance changed",
            },
        )
    )

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
    created = unwrap(response)
    assert created["review_status"] == "unreviewed"

    assert unwrap(client.get("/alerts"))[0]["title"] == "Review guidance"
    assert unwrap(client.get(f"/alerts/{created['id']}"))["event_id"] == event["id"]


def test_create_list_and_get_thesis_note(client: TestClient) -> None:
    company = unwrap(client.post("/companies", json={"ticker": "AMZN", "name": "Amazon"}))

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
    created = unwrap(response)
    assert created["status"] == "active"

    assert unwrap(client.get("/thesis-notes"))[0]["title"] == "AWS thesis"
    assert unwrap(client.get(f"/thesis-notes/{created['id']}"))["company_id"] == company["id"]
