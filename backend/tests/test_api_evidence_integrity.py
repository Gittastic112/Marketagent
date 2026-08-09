from hashlib import sha256
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from datetime import date

from app.models import (
    DocumentAsset,
    Event,
    EventEvidenceReference,
    FinancialExtractionCandidate,
    FinancialStatementPeriod,
    RawDocument,
)
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
