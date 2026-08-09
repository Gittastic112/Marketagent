from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Alert, EventEvidenceReference, ProcessingRun, User
from helpers import response_data


def _event_with_source(
    client: TestClient,
    *,
    ticker: str,
    source_text: str,
    description: str | None,
) -> tuple[dict, dict]:
    company = response_data(client.post("/companies", json={"ticker": ticker, "name": f"{ticker} Co"}))
    source = response_data(client.post("/sources", json={"name": f"{ticker} filing", "source_type": "filing"}))
    document = response_data(client.post("/raw-documents", json={
        "company_id": company["id"],
        "source_id": source["id"],
        "document_type": "annual_report",
        "title": f"{ticker} annual report",
        "published_at": "2026-08-01T00:00:00Z",
        "raw_text": source_text,
        "content_hash": f"{ticker.lower()}-backfill-source",
    }))
    event = response_data(client.post("/events", json={
        "company_id": company["id"],
        "raw_document_id": document["id"],
        "event_type": "filing_update",
        "information_speed": "slow",
        "title": f"{ticker} source-backed event",
        "description": description,
        "priority_score": 80,
    }))
    return document, event


def test_event_evidence_backfill_previews_and_applies_one_exact_span(
    client: TestClient,
    db_session: Session,
) -> None:
    claim = "Consolidated revenue increased by eighteen percent year over year."
    document, event = _event_with_source(
        client,
        ticker="BACKFILL",
        source_text=f"Opening section. {claim} Closing section.",
        description=claim,
    )

    preview = response_data(client.get("/data-health/event-evidence-backfill?limit=25"))
    entry = next(item for item in preview["entries"] if item["event_id"] == event["id"])
    assert preview["dry_run"] is True
    assert preview["processing_run_id"] is None
    assert entry["status"] == "eligible"
    assert entry["claim_origin"] == "event.description"
    assert document["raw_text"][entry["start_char"]:entry["end_char"]] == claim

    dry_run = response_data(client.post("/data-health/event-evidence-backfill", json={
        "dry_run": True,
        "event_ids": [event["id"]],
    }))
    assert dry_run["eligible_count"] == 1
    assert dry_run["applied_count"] == 0
    assert db_session.query(EventEvidenceReference).filter_by(event_id=event["id"]).count() == 0

    applied = response_data(client.post("/data-health/event-evidence-backfill", json={
        "dry_run": False,
        "event_ids": [event["id"]],
    }))
    assert applied["applied_count"] == 1
    assert applied["entries"][0]["status"] == "applied"
    reference = db_session.query(EventEvidenceReference).filter_by(event_id=event["id"]).one()
    assert reference.locator_type == "text_span"
    assert reference.quote == claim
    assert reference.origin == "deterministic_backfill"
    assert reference.source_metadata_json["processing_run_id"] == applied["processing_run_id"]

    run = db_session.get(ProcessingRun, applied["processing_run_id"])
    assert run is not None
    assert run.run_type == "event_evidence_backfill"
    assert run.status == "success"
    assert run.created_count == 1
    assert run.metadata_json["eligible_count"] == 1

    after = response_data(client.get("/data-health/event-evidence-backfill?limit=25"))
    assert all(item["event_id"] != event["id"] for item in after["entries"])


def test_event_evidence_backfill_rejects_ambiguous_and_conflicting_matches(
    client: TestClient,
) -> None:
    repeated = "Operating cash flow improved materially during the reported period."
    _, ambiguous_event = _event_with_source(
        client,
        ticker="AMBIG",
        source_text=f"{repeated} Other text. {repeated}",
        description=repeated,
    )
    description = "Management increased the full-year revenue growth outlook."
    alert_claim = "The company also reduced expected capital expenditure for the year."
    _, conflict_event = _event_with_source(
        client,
        ticker="CONFLICT",
        source_text=f"{description} {alert_claim}",
        description=description,
    )
    response_data(client.post("/alerts", json={
        "event_id": conflict_event["id"],
        "alert_type": "filing_alert",
        "title": "Conflicting exact claim",
        "evidence": alert_claim,
    }))

    preview = response_data(client.get("/data-health/event-evidence-backfill?limit=50"))
    by_event = {entry["event_id"]: entry for entry in preview["entries"]}

    assert by_event[ambiguous_event["id"]]["status"] == "ambiguous_match"
    assert by_event[ambiguous_event["id"]]["occurrence_count"] == 2
    assert by_event[conflict_event["id"]]["status"] == "conflicting_exact_matches"


def test_event_evidence_backfill_does_not_read_another_users_alert_evidence(
    client: TestClient,
    db_session: Session,
) -> None:
    private_claim = "Private alert evidence appears exactly once in this source document."
    _, event = _event_with_source(
        client,
        ticker="OWNED",
        source_text=private_claim,
        description="This event description intentionally does not match the stored source.",
    )
    db_session.add(User(id="other-backfill-user", email="other-backfill@example.com", name="Other"))
    db_session.add(Alert(
        user_id="other-backfill-user",
        event_id=event["id"],
        alert_type="private_alert",
        title="Private alert",
        evidence=private_claim,
    ))
    db_session.commit()

    preview = response_data(client.post("/data-health/event-evidence-backfill", json={
        "dry_run": True,
        "event_ids": [event["id"]],
    }))

    assert preview["eligible_count"] == 0
    assert preview["entries"][0]["status"] == "no_exact_match"
    assert "Private alert" not in str(preview)


def test_event_evidence_backfill_validates_bounded_unique_event_ids(client: TestClient) -> None:
    duplicate = client.post("/data-health/event-evidence-backfill", json={
        "dry_run": True,
        "event_ids": [1, 1],
    })
    too_large = client.get("/data-health/event-evidence-backfill?limit=201")
    empty = client.post("/data-health/event-evidence-backfill", json={
        "dry_run": True,
        "event_ids": [],
    })

    assert duplicate.status_code == 422
    assert too_large.status_code == 422
    assert empty.status_code == 422
