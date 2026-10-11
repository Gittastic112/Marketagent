from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Company, Event, ProcessingRun
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

    with TestingSessionLocal() as db:
        company = Company(ticker="AAPL", name="Apple Inc.")
        event = Event(
            company=company,
            event_type="manual_event",
            information_speed="medium",
            title="Manual event for brief",
            priority_score=90,
        )
        failed_run = ProcessingRun(
            run_type="sec_ingestion",
            source_type="sec",
            source_id=None,
            company_id=None,
            started_at=datetime.now(UTC),
            finished_at=datetime.now(UTC),
            status="failed",
            error_count=1,
            error_details_json={"errors": ["private provider detail must stay out of the brief"]},
        )
        db.add_all([company, event, failed_run])
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


def test_get_daily_brief_returns_rule_based_brief(client: TestClient) -> None:
    response = client.get("/daily-brief")

    assert response.status_code == 200
    body = response_data(response)
    assert body["title"] == "Daily Intelligence Brief"
    assert body["review_status"] == "new"
    assert body["payload_json"]["new_since_last_review"] is not None
    assert body["payload_json"]["thesis_contradictions"] == []
    assert body["payload_json"]["valuation_analysis_status"] == "not_run"
    assert body["payload_json"]["processing_failures"] == [
        {
            "processing_run_id": body["payload_json"]["processing_failures"][0]["processing_run_id"],
            "run_type": "sec_ingestion",
            "source_type": "sec",
            "status": "failed",
            "error_count": 1,
            "started_at": body["payload_json"]["processing_failures"][0]["started_at"],
            "finished_at": body["payload_json"]["processing_failures"][0]["finished_at"],
            "claim_type": "Fact",
        }
    ]
    assert "private provider detail" not in str(body["payload_json"]["processing_failures"])
    inspection_queue = body["payload_json"]["inspection_queue"]
    processing_action = next(item for item in inspection_queue if item["action_type"] == "inspect_processing_failure")
    assert processing_action["href"] == "/data-health"
    assert processing_action["processing_run_id"] == body["payload_json"]["processing_failures"][0]["processing_run_id"]
    assert processing_action["claim_type"] == "Calculation"

    manual_event = body["payload_json"]["high_materiality_events"][0]
    evidence_action = next(item for item in inspection_queue if item["action_type"] == "resolve_event_evidence")
    assert evidence_action["source_event_ids"] == [manual_event["event_id"]]
    assert evidence_action["source_raw_document_ids"] == []
    assert evidence_action["href"] == f'/events/{manual_event["event_id"]}/evidence-resolution'
    assert response.json()["meta"]["source"] == "stored_events_alerts_holdings_prices_and_reviewed_ai_outputs"
    assert response.json()["meta"]["is_mock"] is False
    assert response.json()["meta"]["is_stale"] is False

    repeated = response_data(client.get("/daily-brief"))
    assert repeated["id"] == body["id"]


def test_post_daily_brief_persists_brief(client: TestClient) -> None:
    response = client.post("/daily-brief")

    assert response.status_code == 201
    body = response_data(response)
    assert body["title"] == "Daily Intelligence Brief"
    assert body["review_status"] == "new"
    assert body["payload_json"]["thesis_contradictions"] == []


def test_list_saved_daily_briefs_returns_recent_saved_briefs(client: TestClient) -> None:
    client.post("/daily-brief")

    response = client.get("/daily-brief-history")

    assert response.status_code == 200
    body = response_data(response)
    assert len(body) == 1
    assert body[0]["title"] == "Daily Intelligence Brief"


def test_review_daily_brief_updates_status(client: TestClient) -> None:
    post_res = client.post("/daily-brief")
    brief_id = response_data(post_res)["id"]
    assert response_data(post_res)["review_status"] == "new"

    patch_res = client.patch(f"/daily-brief/{brief_id}/review")
    assert patch_res.status_code == 200
    assert response_data(patch_res)["review_status"] == "reviewed"
    assert response_data(patch_res)["reviewed_at"] is not None

    history = response_data(client.get("/daily-brief-history"))
    reviewed = next(brief for brief in history if brief["id"] == brief_id)
    assert reviewed["reviewed_at"] == response_data(patch_res)["reviewed_at"]
