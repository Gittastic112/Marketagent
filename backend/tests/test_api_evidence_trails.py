from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.dcf import DcfAssumptionSet, ValuationAssumptionChangeLog, ValuationModel
from app.models.thesis_note import EventThesisImpact, ThesisAssumption, ThesisNote
from app.models.user import User
from app.models import DocumentAsset, EventEvidenceReference
from helpers import response_data


PDF_FIXTURE = Path(__file__).parent / "fixtures" / "financial_statement_table.pdf"


def create_source_backed_alert(client: TestClient) -> tuple[dict, dict, dict]:
    evidence_quote = "Gross margin increased by two percentage points."
    source_text = f"PRIVATE_FULL_DOCUMENT_BODY must never leave the evidence endpoint. {evidence_quote}"
    company = response_data(
        client.post(
            "/companies",
            json={
                "ticker": "EVID",
                "name": "Evidence Corp",
                "market": "US",
                "primary_exchange": "NYSE",
                "local_symbol": "EVID",
            },
        )
    )
    source = response_data(
        client.post(
            "/sources",
            json={
                "name": "Evidence Wire",
                "source_type": "filing",
                "base_url": "https://example.com",
                "reliability_score": 90,
            },
        )
    )
    document = response_data(
        client.post(
            "/raw-documents",
            json={
                "company_id": company["id"],
                "source_id": source["id"],
                "document_type": "10-Q",
                "title": "Evidence Corp Q2 filing",
                "url": "https://example.com/evid-q2",
                "published_at": "2026-07-20T12:00:00Z",
                "raw_text": source_text,
                "raw_payload_json": {"private_provider_field": "do-not-serialize"},
                "content_hash": "evidence-trail-document-hash",
            },
        )
    )
    event = response_data(
        client.post(
            "/events",
            json={
                "company_id": company["id"],
                "raw_document_id": document["id"],
                "event_type": "filing_update",
                "information_speed": "medium",
                "title": "Margins changed",
                "description": "Reported gross margin increased by two percentage points.",
                "event_time": "2026-07-20T12:00:00Z",
                "credibility_score": 92,
                "priority_score": 78,
            },
        )
    )
    start_char = source_text.index(evidence_quote)
    reference_response = client.post(
        f"/events/{event['id']}/evidence-references",
        json={
            "raw_document_id": document["id"],
            "locator_type": "text_span",
            "start_char": start_char,
            "end_char": start_char + len(evidence_quote),
            "quote": evidence_quote,
            "confidence_label": "high",
        },
    )
    assert reference_response.status_code == 201
    alert = response_data(
        client.post(
            "/alerts",
            json={
                "company_id": company["id"],
                "event_id": event["id"],
                "alert_type": "filing_alert",
                "severity": "medium",
                "title": "Review the margin change",
                "summary": "Margins changed in the latest filing.",
                "why_it_matters": "The change may affect the operating-margin thesis.",
                "evidence": "Gross margin increased by two percentage points.",
                "confidence_bucket": "high",
            },
        )
    )
    return company, event, alert


def test_alert_evidence_trail_is_typed_source_backed_and_bounded(client: TestClient) -> None:
    company, event, alert = create_source_backed_alert(client)

    response = client.get(f"/alerts/{alert['id']}/evidence-trail")

    assert response.status_code == 200
    trail = response_data(response)
    assert trail["entry_point"] == "alert"
    assert trail["claim_type"] == "Source Summary"
    assert trail["evidence_status"] == "complete"
    assert trail["confidence"] == "high"
    assert trail["claim_excerpt"] == "Gross margin increased by two percentage points."
    assert trail["excerpt_origin"] == "event.evidence_reference"
    assert trail["event"]["id"] == event["id"]
    assert trail["company"]["id"] == company["id"]
    assert trail["source"]["name"] == "Evidence Wire"
    assert trail["document"]["has_raw_text"] is True
    assert trail["locator"]["precision"] == "span"
    assert trail["locator"]["quote"] == "Gross margin increased by two percentage points."
    assert "evidence_reference=" in trail["locator"]["internal_href"]
    assert "document-level" not in " ".join(trail["warnings"]).lower()
    assert '"raw_text":' not in response.text
    assert '"raw_payload_json":' not in response.text
    assert "PRIVATE_FULL_DOCUMENT_BODY" not in response.text
    assert response.json()["meta"]["is_mock"] is False


def test_event_evidence_trail_uses_the_same_safe_contract(client: TestClient) -> None:
    _, event, _ = create_source_backed_alert(client)

    response = client.get(f"/events/{event['id']}/evidence-trail")

    assert response.status_code == 200
    trail = response_data(response)
    assert trail["entry_point"] == "event"
    assert trail["alert"] is None
    assert trail["claim_excerpt"] == "Gross margin increased by two percentage points."
    assert trail["excerpt_origin"] == "event.evidence_reference"
    assert "PRIVATE_FULL_DOCUMENT_BODY" not in response.text


def test_pdf_region_requires_reproducible_geometry_and_routes_to_exact_viewer(
    client: TestClient,
    db_session: Session,
) -> None:
    _, event, _ = create_source_backed_alert(client)
    trail = response_data(client.get(f"/events/{event['id']}/evidence-trail"))
    document_id = trail["document"]["id"]
    db_session.query(EventEvidenceReference).filter_by(event_id=event["id"]).delete()
    content = PDF_FIXTURE.read_bytes()
    db_session.add(DocumentAsset(
        raw_document_id=document_id,
        original_filename=PDF_FIXTURE.name,
        mime_type="application/pdf",
        size_bytes=len(content),
        sha256=sha256(content).hexdigest(),
        page_count=1,
        content=content,
    ))
    db_session.commit()
    geometry = {
        "page": 1,
        "coordinate_system": "pdfplumber_top_left_points",
        "page_width": 612,
        "page_height": 792,
        "bounding_box": {"x0": 50, "top": 100, "x1": 550, "bottom": 130},
    }

    missing = client.post(f"/events/{event['id']}/evidence-references", json={
        "raw_document_id": document_id,
        "locator_type": "pdf_region",
        "source_page": 1,
    })
    assert missing.status_code == 422
    assert "requires bounding_box_json" in missing.json()["detail"]

    wrong_dimensions = client.post(f"/events/{event['id']}/evidence-references", json={
        "raw_document_id": document_id,
        "locator_type": "pdf_region",
        "source_page": 1,
        "bounding_box_json": {**geometry, "page_width": 700},
    })
    assert wrong_dimensions.status_code == 422
    assert "do not match" in wrong_dimensions.json()["detail"]

    created = client.post(f"/events/{event['id']}/evidence-references", json={
        "raw_document_id": document_id,
        "locator_type": "pdf_region",
        "source_page": 1,
        "quote": "Revenue and profit rows",
        "bounding_box_json": geometry,
        "confidence_label": "high",
    })
    assert created.status_code == 201
    reference = response_data(created)
    assert reference["bounding_box_json"]["coordinate_system"] == "pdfplumber_top_left_points"
    assert reference["pdf_region_status"] == "valid"
    assert response_data(client.get(f"/evidence-references/{reference['id']}"))["pdf_region_status"] == "valid"

    exact_trail = response_data(client.get(f"/events/{event['id']}/evidence-trail"))
    assert exact_trail["evidence_status"] == "complete"
    assert exact_trail["locator"]["precision"] == "region"
    assert exact_trail["locator"]["internal_href"] == (
        f"/documents/{document_id}/event-evidence?evidence_reference={reference['id']}"
    )


def test_text_span_reference_must_match_stored_source(client: TestClient) -> None:
    _, event, _ = create_source_backed_alert(client)
    trail = response_data(client.get(f"/events/{event['id']}/evidence-trail"))

    response = client.post(
        f"/events/{event['id']}/evidence-references",
        json={
            "raw_document_id": trail["document"]["id"],
            "locator_type": "text_span",
            "start_char": 0,
            "end_char": 8,
            "quote": "invented",
        },
    )

    assert response.status_code == 422
    assert "does not match" in response.json()["detail"]


def test_alert_evidence_trail_reports_missing_linkage(client: TestClient) -> None:
    alert = response_data(
        client.post(
            "/alerts",
            json={
                "alert_type": "manual_alert",
                "title": "Unlinked research note",
                "summary": "This has not been connected to an event.",
                "confidence_bucket": "low",
            },
        )
    )

    trail = response_data(client.get(f"/alerts/{alert['id']}/evidence-trail"))

    assert trail["claim_type"] == "User Assumption"
    assert trail["evidence_status"] == "missing"
    assert trail["event"] is None
    assert trail["document"] is None
    assert trail["locator"]["precision"] == "none"
    assert "not linked to an event" in " ".join(trail["warnings"]).lower()


def test_alert_evidence_enforces_alert_and_impact_ownership(
    client: TestClient,
    db_session: Session,
) -> None:
    company, event, alert = create_source_backed_alert(client)
    db_session.add(User(id="other-user", email="other@example.com", name="Other User"))
    current_note = ThesisNote(
        user_id="admin_user_id_fallback",
        company_id=company["id"],
        title="Current thesis",
        thesis_text="Margin durability matters.",
    )
    other_note = ThesisNote(
        user_id="other-user",
        company_id=company["id"],
        title="Private other thesis",
        thesis_text="This must remain private.",
    )
    db_session.add_all([current_note, other_note])
    db_session.flush()
    current_assumption = ThesisAssumption(
        thesis_note_id=current_note.id,
        description="Gross margin remains durable.",
        status="active",
    )
    other_assumption = ThesisAssumption(
        thesis_note_id=other_note.id,
        description="Private assumption.",
        status="active",
    )
    db_session.add_all([current_assumption, other_assumption])
    db_session.flush()
    db_session.add_all(
        [
            EventThesisImpact(
                event_id=event["id"],
                thesis_assumption_id=current_assumption.id,
                impact_classification="Supports",
                rationale="The reported margin supports the assumption.",
            ),
            EventThesisImpact(
                event_id=event["id"],
                thesis_assumption_id=other_assumption.id,
                impact_classification="Weakens",
                rationale="PRIVATE_OTHER_USER_RATIONALE",
            ),
        ]
    )

    current_model = ValuationModel(
        user_id="admin_user_id_fallback",
        company_id=company["id"],
        name="Current valuation",
    )
    other_model = ValuationModel(
        user_id="other-user",
        company_id=company["id"],
        name="Private other valuation",
    )
    db_session.add_all([current_model, other_model])
    db_session.flush()
    current_set = DcfAssumptionSet(valuation_model_id=current_model.id, scenario="Base")
    other_set = DcfAssumptionSet(valuation_model_id=other_model.id, scenario="Base")
    db_session.add_all([current_set, other_set])
    db_session.flush()
    db_session.add_all(
        [
            ValuationAssumptionChangeLog(
                valuation_model_id=current_model.id,
                assumption_set_id=current_set.id,
                event_id=event["id"],
                parameter_name="target_operating_margin",
                old_value="0.20",
                new_value="0.22",
                rationale="Reviewed filing evidence.",
            ),
            ValuationAssumptionChangeLog(
                valuation_model_id=other_model.id,
                assumption_set_id=other_set.id,
                event_id=event["id"],
                parameter_name="terminal_growth_rate",
                rationale="PRIVATE_OTHER_USER_VALUATION",
            ),
        ]
    )
    other_alert = Alert(
        user_id="other-user",
        event_id=event["id"],
        company_id=company["id"],
        alert_type="private_alert",
        title="Private other alert",
        created_at=datetime.now(UTC),
    )
    db_session.add(other_alert)
    db_session.commit()

    response = client.get(f"/alerts/{alert['id']}/evidence-trail")
    assert response.status_code == 200
    trail = response_data(response)
    assert [impact["assumption_description"] for impact in trail["thesis_impacts"]] == [
        "Gross margin remains durable."
    ]
    assert [impact["parameter_name"] for impact in trail["valuation_impacts"]] == [
        "target_operating_margin"
    ]
    assert "PRIVATE_OTHER_USER" not in response.text

    forbidden = client.get(f"/alerts/{other_alert.id}/evidence-trail")
    assert forbidden.status_code == 404
