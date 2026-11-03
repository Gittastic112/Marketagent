from hashlib import sha256
from pathlib import Path
import pytest

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from datetime import UTC, date, datetime

from app.models import (
    DocumentAsset,
    Event,
    EventEvidenceReference,
    FinancialExtractionCandidate,
    FinancialStatementPeriod,
    PeerValuationSet,
    RawDocument,
)
from app.models.user import User
from helpers import response_data


PDF_FIXTURE = Path(__file__).parent / "fixtures" / "financial_statement_table.pdf"


def _source_records(client: TestClient, *, ticker: str = "EVID") -> tuple[dict, dict, dict]:
    company = response_data(client.post("/companies", json={"ticker": ticker, "name": f"{ticker} Co"}))
    source = response_data(client.post("/sources", json={"name": f"{ticker} filing", "source_type": "filing"}))
    text = "Revenue increased by 18 percent year over year."
    document = response_data(client.post("/raw-documents", json={
        "company_id": company["id"],
        "source_id": source["id"],
        "document_type": "10-K",
        "title": f"{ticker} annual filing",
        "published_at": "2026-07-30T12:00:00Z",
        "raw_text": text,
        "content_hash": f"{ticker.lower()}-evidence-integrity",
    }))
    event = response_data(client.post("/events", json={
        "company_id": company["id"],
        "raw_document_id": document["id"],
        "event_type": "filing",
        "information_speed": "slow",
        "title": f"{ticker} revenue update",
    }))
    return company, document, event


def test_evidence_integrity_reports_valid_exact_reference(client: TestClient) -> None:
    _, document, event = _source_records(client)
    quote = "Revenue increased"
    response_data(client.post(f'/events/{event["id"]}/evidence-references', json={
        "raw_document_id": document["id"],
        "locator_type": "text_span",
        "start_char": 0,
        "end_char": len(quote),
        "quote": quote,
        "confidence_label": "high",
    }))

    report = response_data(client.get("/data-health/evidence-integrity"))

    assert report["status"] == "healthy"
    assert report["checked_documents"] == 1
    assert report["checked_references"] == 1
    assert report["error_count"] == 0
    assert report["financial_certification_status"] == "not_available"
    assert report["issues"] == []


def test_evidence_integrity_supports_fast_metadata_scope(client: TestClient) -> None:
    _source_records(client, ticker="FAST")

    response = client.get("/data-health/evidence-integrity?deep=false")
    report = response_data(response)

    assert report["verification_scope"] == "metadata"
    assert report["asset_content_verification_status"] == "not_run"
    assert report["limitations"] == [
        "Asset byte/hash verification and PDF-region geometry checks were not run in metadata scope."
    ]
    assert response.json()["meta"]["warnings"] == report["limitations"]


def test_evidence_integrity_uses_ingestion_time_for_xbrl_retrieval_snapshots(
    client: TestClient,
) -> None:
    company = response_data(client.post(
        "/companies",
        json={"ticker": "XBRL", "name": "XBRL Co"},
    ))
    source = response_data(client.post(
        "/sources",
        json={"name": "SEC Company Facts", "source_type": "sec"},
    ))
    response_data(client.post("/raw-documents", json={
        "company_id": company["id"],
        "source_id": source["id"],
        "document_type": "xbrl_facts",
        "title": "XBRL SEC Company Facts",
        "content_hash": "sec-companyfacts:test-snapshot",
    }))

    report = response_data(client.get("/data-health/evidence-integrity"))

    assert report["status"] == "healthy"
    assert not any(
        issue["code"] == "DOCUMENT_SOURCE_TIMESTAMP_MISSING"
        for issue in report["issues"]
    )


def test_evidence_integrity_rejects_pdf_geometry_that_does_not_match_asset(
    client: TestClient,
    db_session: Session,
) -> None:
    _, document, event = _source_records(client, ticker="PDFBOX")
    content = PDF_FIXTURE.read_bytes()
    db_session.add(DocumentAsset(
        raw_document_id=document["id"],
        original_filename=PDF_FIXTURE.name,
        mime_type="application/pdf",
        size_bytes=len(content),
        sha256=sha256(content).hexdigest(),
        page_count=1,
        content=content,
    ))
    db_session.add(EventEvidenceReference(
        event_id=event["id"],
        raw_document_id=document["id"],
        locator_type="pdf_region",
        source_page=1,
        bounding_box_json={
            "page": 1,
            "coordinate_system": "pdfplumber_top_left_points",
            "page_width": 700,
            "page_height": 792,
            "bounding_box": {"x0": 50, "top": 100, "x1": 550, "bottom": 130},
        },
        confidence_label="high",
        origin="legacy_import",
    ))
    db_session.commit()

    report = response_data(client.get("/data-health/evidence-integrity"))
    issue = next(item for item in report["issues"] if item["code"] == "EVIDENCE_PDF_BOUNDS_INVALID")

    assert report["status"] == "issues_found"
    assert issue["document_id"] == document["id"]
    assert "not reproducible" in issue["message"]


def test_evidence_integrity_finds_corrupt_locators_and_asset_metadata(
    client: TestClient,
    db_session: Session,
) -> None:
    company, document, event = _source_records(client, ticker="BROKEN")
    other_company = response_data(client.post("/companies", json={"ticker": "OTHER", "name": "Other Co"}))
    stored_content = b"stored-pdf-bytes"
    asset = DocumentAsset(
        raw_document_id=document["id"],
        original_filename="broken.pdf",
        mime_type="application/pdf",
        size_bytes=len(stored_content) + 1,
        sha256=sha256(b"different-bytes").hexdigest(),
        page_count=2,
        content=stored_content,
    )
    db_session.add(asset)
    db_session.add(EventEvidenceReference(
        event_id=event["id"],
        raw_document_id=document["id"],
        locator_type="pdf_region",
        source_page=3,
        confidence_label="low",
        origin="manual_review",
    ))
    db_session.commit()
    event_record = db_session.get(Event, event["id"])
    document_record = db_session.get(RawDocument, document["id"])
    assert event_record is not None and document_record is not None
    event_record.company_id = other_company["id"]
    document_record.published_at = None
    db_session.commit()

    response = client.get("/data-health/evidence-integrity")
    report = response_data(response)
    codes = {issue["code"] for issue in report["issues"]}

    assert report["status"] == "issues_found"
    assert report["error_count"] == 4
    assert report["warning_count"] == 3
    assert codes == {
        "ASSET_HASH_MISMATCH",
        "ASSET_SIZE_MISMATCH",
        "DOCUMENT_SOURCE_TIMESTAMP_MISSING",
        "EVIDENCE_COMPANY_MISMATCH",
        "EVIDENCE_CONFIDENCE_LOW",
        "EVIDENCE_PDF_BOUNDS_MISSING",
        "EVIDENCE_PDF_PAGE_INVALID",
    }
    assert response.json()["meta"]["source"] == "internal_evidence_audit"
    assert response.json()["meta"]["warnings"] == ["Evidence integrity found 4 blocking error(s)."]


def test_evidence_integrity_detects_promoted_financial_period_mismatch(
    client: TestClient,
    db_session: Session,
) -> None:
    company, document, _ = _source_records(client, ticker="FISCAL")
    period = FinancialStatementPeriod(
        company_id=company["id"],
        period_type="annual",
        year=2025,
        report_date=date(2025, 12, 31),
        currency="USD",
        currency_source="reviewed_candidate_unit",
        currency_confidence="high",
    )
    db_session.add(period)
    db_session.flush()
    db_session.add(FinancialExtractionCandidate(
        company_id=company["id"],
        raw_document_id=document["id"],
        metric_code="revenue",
        reported_label="Revenue",
        value=100,
        unit="USD",
        fiscal_year=2025,
        period_type="annual",
        source_text="Revenue increased",
        source_page=1,
        source_locator_json={"type": "pdf_table", "end": "2025-03-31"},
        extraction_method="test_fixture",
        confidence_label="high",
        review_status="promoted",
    ))
    db_session.commit()

    report = response_data(client.get("/data-health/evidence-integrity"))
    codes = {issue["code"] for issue in report["issues"]}

    assert "FINANCIAL_PERIOD_END_MISMATCH" in codes
    assert report["checked_financial_candidates"] == 1
    assert report["financial_certification_status"] == "blocked"


def _peer_members() -> list[dict]:
    return [
        {
            "identifier": f"HEALTH{index}",
            "included": True,
            "multiples": {"pe": 10.0 + index},
            "sourceName": "Reviewed filing",
            "sourceUrl": f"https://filings.example.com/health-{index}",
            "sourceAsOf": date.today().isoformat(),
            "claimType": "Fact",
        }
        for index in range(1, 4)
    ]


def _create_peer_set(client: TestClient, company_id: int, name: str) -> dict:
    return response_data(client.post(
        "/api/valuation/relative/peer-sets",
        json={"companyId": company_id, "name": name, "members": _peer_members()},
    ))


def _review_peer_set(client: TestClient, peer_set: dict) -> dict:
    diagnostics = peer_set["diagnostics"]
    return response_data(client.post(
        f"/api/valuation/relative/peer-sets/{peer_set['id']}/review",
        json={
            "acknowledged": True,
            "expectedVersion": peer_set["version"],
            "expectedDiagnosticsSha256": diagnostics["acknowledgementSha256"],
            "acknowledgedWarningCodes": diagnostics["warningCodes"],
        },
    ))


def test_peer_review_receipt_health_classifies_owned_sets(
    client: TestClient,
    db_session: Session,
) -> None:
    company = response_data(client.post(
        "/companies",
        json={"ticker": "PEERHEALTH", "name": "Peer Health Co"},
    ))
    current = _review_peer_set(client, _create_peer_set(client, company["id"], "Current"))
    missing = _create_peer_set(client, company["id"], "Missing")
    stale = _review_peer_set(client, _create_peer_set(client, company["id"], "Stale"))
    draft = _create_peer_set(client, company["id"], "Draft")
    archived = _create_peer_set(client, company["id"], "Archived")

    missing_record = db_session.get(PeerValuationSet, missing["id"])
    missing_record.review_status = "reviewed"
    missing_record.reviewed_at = datetime.now(UTC)
    stale_record = db_session.get(PeerValuationSet, stale["id"])
    stale_record.review_warning_codes_json = []
    archived_record = db_session.get(PeerValuationSet, archived["id"])
    archived_record.is_active = False
    db_session.add(User(id="other_peer_health_user", email="peer-health@example.com", name="Other"))
    db_session.add(PeerValuationSet(
        company_id=company["id"],
        user_id="other_peer_health_user",
        name="Other owner's stale set",
        peer_identifiers_json=_peer_members(),
        aggregate_metrics_json={},
        aggregation_method="median",
        version=1,
        review_status="reviewed",
        reviewed_at=datetime.now(UTC),
        is_active=True,
    ))
    db_session.commit()

    response = client.get("/data-health/peer-review-receipts")
    report = response_data(response)

    assert report["status"] == "attention_required"
    assert report["checked_set_count"] == 5
    assert report["active_reviewed_set_count"] == 3
    assert report["ready_for_valuation_count"] == 1
    assert report["missing_receipt_count"] == 1
    assert report["stale_receipt_count"] == 1
    assert report["draft_set_count"] == 1
    assert report["archived_set_count"] == 1
    assert [item["peer_set_id"] for item in report["sets_requiring_attention"]] == [
        missing["id"],
        stale["id"],
    ]
    assert {item["receipt_status"] for item in report["sets_requiring_attention"]} == {
        "missing",
        "stale",
    }
    assert current["id"] not in {
        item["peer_set_id"] for item in report["sets_requiring_attention"]
    }
    assert draft["id"] not in {
        item["peer_set_id"] for item in report["sets_requiring_attention"]
    }
    assert archived["id"] not in {
        item["peer_set_id"] for item in report["sets_requiring_attention"]
    }
    assert response.json()["meta"]["warnings"] == [
        "2 active reviewed peer set(s) need diagnostic re-acknowledgement."
    ]


def test_peer_review_receipt_health_has_explicit_empty_state(client: TestClient) -> None:
    response = client.get("/data-health/peer-review-receipts")
    report = response_data(response)

    assert response.status_code == 200
    assert report["status"] == "healthy"
    assert report["checked_set_count"] == 0
    assert report["sets_requiring_attention"] == []
    assert response.json()["meta"]["warnings"] == []


@pytest.mark.parametrize("storage", ["member", "target"])
def test_receipt_health_does_not_call_conflicting_evidence_ready(client, db_session, storage):
    company = response_data(client.post("/companies", json={"ticker": "CONFLICT", "name": "Conflict"}))
    reviewed = _review_peer_set(client, _create_peer_set(client, company["id"], "Conflicting"))
    record = db_session.get(PeerValuationSet, reviewed["id"])
    if storage == "member":
        record.peer_identifiers_json = [{**m, "sourceName": "Conflicting source"} for m in record.peer_identifiers_json]
    else:
        from app.models import PeerValuationTargetProfile
        record.target_profile = PeerValuationTargetProfile(
            source_name="Target filing", source_url="https://example.com/target",
            source_as_of=date.today(), claim_type="Fact", currency="USD",
        )
    db_session.commit()
    report = response_data(client.get("/data-health/peer-review-receipts"))
    assert report["ready_for_valuation_count"] == 0
    assert report["storage_blocked_count"] == 1
    item = report["sets_requiring_attention"][0]
    assert f"{storage}_storage_mismatch" in item["blockers"]
    assert "repair" in item["action"].lower()


def test_receipt_health_cursor_pages_cover_owned_sets_without_duplicates(client, db_session):
    company = response_data(client.post("/companies", json={"ticker": "PAGES", "name": "Pages"}))
    ids = [_create_peer_set(client, company["id"], f"Draft {i}")["id"] for i in range(3)]
    first = response_data(client.get("/data-health/peer-review-receipts?limit=2"))
    assert first["total_owned_set_count"] == 3
    assert first["checked_set_count"] == 2
    assert first["next_after_id"] == ids[1]
    assert first["has_more"] is True
    assert first["scope"] == "page"
    second = response_data(client.get(f"/data-health/peer-review-receipts?limit=2&after_id={first['next_after_id']}"))
    assert second["checked_set_count"] == 1
    assert second["draft_set_count"] == 1
    assert second["next_after_id"] is None
    assert second["has_more"] is False
    assert second["total_owned_set_count"] == 3


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "after_id=-1", "after_id=abc"])
def test_receipt_health_rejects_invalid_paging(client, query):
    assert client.get(f"/data-health/peer-review-receipts?{query}").status_code == 422


def test_receipt_health_cursor_beyond_last_is_empty_not_global_success(client):
    company = response_data(client.post("/companies", json={"ticker": "ENDPAGE", "name": "End"}))
    _create_peer_set(client, company["id"], "Draft")
    report = response_data(client.get("/data-health/peer-review-receipts?after_id=99999"))
    assert report["checked_set_count"] == 0
    assert report["total_owned_set_count"] == 1
    assert report["scope"] == "page"
    assert report["has_more"] is False


def test_receipt_audit_is_read_only_and_uses_bounded_queries(client, db_session):
    from sqlalchemy import event
    company = response_data(client.post("/companies", json={"ticker": "READONLY", "name": "Read only"}))
    created = _create_peer_set(client, company["id"], "Unchanged")
    reviewed = _review_peer_set(client, created)
    for i in range(3):
        _create_peer_set(client, company["id"], f"Page {i}")
    statements = []
    def capture(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)
    event.listen(db_session.bind, "before_cursor_execute", capture)
    try:
        report = response_data(client.get("/data-health/peer-review-receipts?limit=1"))
    finally:
        event.remove(db_session.bind, "before_cursor_execute", capture)
    assert report["checked_set_count"] == 1
    assert len(statements) <= 4
    assert all(s.lstrip().upper().startswith("SELECT") for s in statements)
    assert any("LIMIT" in s.upper() for s in statements)
    current = response_data(client.get(f"/api/valuation/relative/peer-sets/{created['id']}"))
    assert current["version"] == reviewed["version"]
    assert current["reviewReceipt"] == reviewed["reviewReceipt"]


def test_receipt_cursor_does_not_leak_other_owner_counts(client, db_session):
    company = response_data(client.post("/companies", json={"ticker": "OWNCURSOR", "name": "Owned"}))
    owned = _create_peer_set(client, company["id"], "Owned")
    db_session.add(User(id="private_cursor_user", email="cursor@example.com", name="Private"))
    db_session.add(PeerValuationSet(company_id=company["id"], user_id="private_cursor_user", name="Private", peer_identifiers_json=[]))
    db_session.commit()
    report = response_data(client.get(f"/data-health/peer-review-receipts?after_id={owned['id']}&limit=1"))
    assert report["checked_set_count"] == 0
    assert report["total_owned_set_count"] == 1
    assert report["has_more"] is False
    assert report["next_after_id"] is None
