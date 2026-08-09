from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Event, EventEvidenceReference, RawDocument
from helpers import response_data, response_errors


def _source_event(
    client: TestClient,
    *,
    ticker: str,
    source_text: str,
) -> tuple[dict, dict]:
    company = response_data(client.post("/companies", json={
        "ticker": ticker,
        "name": f"{ticker} Company",
        "market": "US",
        "country": "United States",
        "currency": "USD",
    }))
    source = response_data(client.post("/sources", json={
        "name": f"{ticker} filing",
        "source_type": "filing",
    }))
    document = response_data(client.post("/raw-documents", json={
        "company_id": company["id"],
        "source_id": source["id"],
        "document_type": "annual_report",
        "title": f"{ticker} annual report",
        "raw_text": source_text,
        "content_hash": f"{ticker.lower()}-resolution-source-v1",
    }))
    event = response_data(client.post("/events", json={
        "company_id": company["id"],
        "raw_document_id": document["id"],
        "event_type": "filing_update",
        "information_speed": "slow",
        "title": f"{ticker} evidence review",
        "description": "Management discussed the source claim in the annual filing.",
    }))
    return document, event


def _resolution_payload(search: dict, occurrence_index: int = 1) -> dict:
    match = search["matches"][occurrence_index - 1]
    return {
        "raw_document_id": search["raw_document_id"],
        "start_char": match["start_char"],
        "end_char": match["end_char"],
        "quote": match["quote"],
        "search_query": search["query"],
        "occurrence_index": match["occurrence_index"],
        "document_content_hash": search["document_content_hash"],
    }


def test_exact_search_returns_bounded_context_and_occurrence_metadata(client: TestClient) -> None:
    query = "Operating margin expanded during the period."
    source_text = "START_SECRET" + ("A" * 100) + (f" {query} separator" * 30) + ("Z" * 100) + "END_SECRET"
    document, event = _source_event(client, ticker="BOUNDED", source_text=source_text)

    result = response_data(client.get(
        f"/events/{event['id']}/evidence-resolution/search",
        params={"q": query, "context_chars": 40, "limit": 25},
    ))

    assert result["raw_document_id"] == document["id"]
    assert result["exact_match_count"] == 30
    assert result["returned_match_count"] == 25
    assert result["is_truncated"] is True
    assert [match["occurrence_index"] for match in result["matches"]] == list(range(1, 26))
    assert all(len(match["context_before"]) <= 40 for match in result["matches"])
    assert all(len(match["context_after"]) <= 40 for match in result["matches"])
    assert all(source_text[match["start_char"]:match["end_char"]] == query for match in result["matches"])
    assert "START_SECRET" not in str(result["matches"])
    assert "END_SECRET" not in str(result["matches"])
    assert "raw_text" not in result


def test_manual_resolution_revalidates_and_records_owned_provenance(
    client: TestClient,
    db_session: Session,
) -> None:
    query = "Container volumes increased by twelve percent."
    document, event = _source_event(
        client,
        ticker="RESOLVE",
        source_text=f"First: {query} Second: {query}",
    )
    search = response_data(client.get(
        f"/events/{event['id']}/evidence-resolution/search",
        params={"q": query},
    ))

    created = response_data(client.post(
        f"/events/{event['id']}/evidence-resolution",
        json=_resolution_payload(search, occurrence_index=2),
    ))

    assert created["origin"] == "manual_exact_resolution"
    assert created["created_by_user_id"] == "admin_user_id_fallback"
    assert created["raw_document_id"] == document["id"]
    assert created["quote"] == query
    assert created["source_metadata_json"] == {
        "resolution_method": "manual_exact_case_sensitive_search",
        "search_query": query,
        "occurrence_index": 2,
        "validated_content_hash": document["content_hash"],
    }
    reference = db_session.get(EventEvidenceReference, created["id"])
    assert reference is not None
    assert reference.created_by_user_id == "admin_user_id_fallback"


def test_manual_resolution_rejects_duplicate_and_changed_source(
    client: TestClient,
    db_session: Session,
) -> None:
    query = "Free cash flow improved in the fiscal year."
    document, event = _source_event(client, ticker="RACE", source_text=f"Prefix {query} Suffix")
    search = response_data(client.get(
        f"/events/{event['id']}/evidence-resolution/search",
        params={"q": query},
    ))
    payload = _resolution_payload(search)
    first = client.post(f"/events/{event['id']}/evidence-resolution", json=payload)
    duplicate = client.post(f"/events/{event['id']}/evidence-resolution", json=payload)

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert response_errors(duplicate)[0]["code"] == "EVIDENCE_RESOLUTION_DUPLICATE"

    second_document, second_event = _source_event(
        client,
        ticker="CHANGED",
        source_text=f"Prefix {query} Suffix",
    )
    changed_search = response_data(client.get(
        f"/events/{second_event['id']}/evidence-resolution/search",
        params={"q": query},
    ))
    stored_document = db_session.get(RawDocument, second_document["id"])
    stored_document.content_hash = "changed-content-hash"
    db_session.commit()
    changed = client.post(
        f"/events/{second_event['id']}/evidence-resolution",
        json=_resolution_payload(changed_search),
    )

    assert changed.status_code == 409
    assert response_errors(changed)[0]["code"] == "EVIDENCE_RESOLUTION_SOURCE_CHANGED"


def test_manual_resolution_rejects_document_company_and_span_mismatches(
    client: TestClient,
    db_session: Session,
) -> None:
    query = "Revenue growth remained resilient through the year."
    document, event = _source_event(client, ticker="MISMATCH", source_text=f"Prefix {query} Suffix")
    search = response_data(client.get(
        f"/events/{event['id']}/evidence-resolution/search",
        params={"q": query},
    ))
    payload = _resolution_payload(search)

    wrong_document = {**payload, "raw_document_id": document["id"] + 999}
    mismatch = client.post(f"/events/{event['id']}/evidence-resolution", json=wrong_document)

    shifted = {**payload, "start_char": payload["start_char"] + 1, "end_char": payload["end_char"] + 1}
    span_changed = client.post(f"/events/{event['id']}/evidence-resolution", json=shifted)

    other_company = response_data(client.post("/companies", json={
        "ticker": "OTHERCO",
        "name": "Other Company",
        "market": "US",
    }))
    stored_event = db_session.get(Event, event["id"])
    stored_event.company_id = other_company["id"]
    db_session.commit()
    company_mismatch = client.post(f"/events/{event['id']}/evidence-resolution", json=payload)

    assert mismatch.status_code == 422
    assert response_errors(mismatch)[0]["code"] == "EVIDENCE_RESOLUTION_DOCUMENT_MISMATCH"
    assert span_changed.status_code == 409
    assert response_errors(span_changed)[0]["code"] == "EVIDENCE_RESOLUTION_SPAN_CHANGED"
    assert company_mismatch.status_code == 422
    assert response_errors(company_mismatch)[0]["code"] == "EVIDENCE_RESOLUTION_COMPANY_MISMATCH"


def test_resolution_reports_missing_source_and_validates_query_bounds(client: TestClient) -> None:
    company = response_data(client.post("/companies", json={
        "ticker": "NOSOURCE",
        "name": "No Source Company",
        "market": "US",
    }))
    event = response_data(client.post("/events", json={
        "company_id": company["id"],
        "event_type": "manual",
        "information_speed": "slow",
        "title": "No source event",
    }))

    missing = client.get(
        f"/events/{event['id']}/evidence-resolution/search",
        params={"q": "long enough query"},
    )
    too_short = client.get(
        f"/events/{event['id']}/evidence-resolution/search",
        params={"q": "short"},
    )
    whitespace = client.get(
        f"/events/{event['id']}/evidence-resolution/search",
        params={"q": "        "},
    )

    assert missing.status_code == 409
    assert response_errors(missing)[0]["code"] == "EVIDENCE_RESOLUTION_DOCUMENT_MISSING"
    assert too_short.status_code == 422
    assert whitespace.status_code == 422
    assert response_errors(whitespace)[0]["code"] == "EVIDENCE_RESOLUTION_QUERY_EMPTY"
