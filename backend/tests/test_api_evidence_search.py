from datetime import UTC, datetime

from sqlalchemy import event as sqlalchemy_event

from app.api.dependencies import get_current_user
from app.api.routers.search import (
    SEARCH_QUERY_BUDGET,
    SEARCH_RESPONSE_BUDGET_MS,
    normalize_search_timestamp,
)
from app.main import app
from helpers import response_data


def test_search_timestamp_normalization_supports_mixed_model_columns():
    naive = datetime(2026, 8, 1, 9, 30)
    aware = datetime(2026, 8, 1, 9, 30, tzinfo=UTC)

    assert normalize_search_timestamp(naive) == aware
    assert normalize_search_timestamp(aware) == aware


def test_evidence_search_returns_source_and_exact_stored_span(client):
    company = response_data(client.post("/companies", json={"ticker": "SRCH", "name": "Search Co"}))
    source = response_data(client.post("/sources", json={"name": "Search filing source", "source_type": "filing"}))
    text = "Operating margin expanded by 240 basis points after pricing improved."
    document = response_data(client.post("/raw-documents", json={
        "company_id": company["id"],
        "source_id": source["id"],
        "document_type": "10-Q",
        "title": "Quarterly margin filing",
        "raw_text": text,
        "content_hash": "evidence-search-document",
    }))
    response_data(client.post("/events", json={
        "company_id": company["id"],
        "raw_document_id": document["id"],
        "event_type": "filing_update",
        "information_speed": "medium",
        "title": "Operating margin expansion",
        "description": "Margin expanded in the quarter.",
    }))

    results = response_data(client.get("/search/evidence?q=margin"))

    document_result = next(item for item in results if item["result_type"] == "document")
    assert document_result["source_name"] == "Search filing source"
    assert document_result["claim_type"] == "Fact"
    assert document_result["locator"]["quote"] == "margin"
    assert text[document_result["locator"]["start_char"]:document_result["locator"]["end_char"]] == "margin"
    assert any(item["result_type"] == "event" for item in results)


def test_evidence_search_company_filter_excludes_other_companies(client):
    first = response_data(client.post("/companies", json={"ticker": "ONE", "name": "One"}))
    second = response_data(client.post("/companies", json={"ticker": "TWO", "name": "Two"}))
    source = response_data(client.post("/sources", json={"name": "Filter source", "source_type": "manual"}))
    for company, suffix in ((first, "one"), (second, "two")):
        response_data(client.post("/raw-documents", json={
            "company_id": company["id"],
            "source_id": source["id"],
            "document_type": "note",
            "title": f"Searchable catalyst {suffix}",
            "raw_text": "Searchable catalyst evidence.",
            "content_hash": f"search-filter-{suffix}",
        }))

    results = response_data(client.get(f"/search/evidence?q=catalyst&company_id={first['id']}"))

    assert results
    assert {item["company_id"] for item in results} == {first["id"]}


def test_evidence_search_includes_owned_research_records_and_filters_types(client, db_session):
    company = response_data(client.post("/companies", json={"ticker": "OWND", "name": "Owned Search"}))
    thesis = response_data(client.post("/thesis-notes", json={
        "company_id": company["id"],
        "title": "Durable conviction thesis",
        "thesis_text": "Conviction depends on recurring revenue durability.",
    }))
    alert = response_data(client.post("/alerts", json={
        "company_id": company["id"],
        "alert_type": "manual",
        "title": "Conviction evidence changed",
        "summary": "New evidence changes conviction.",
    }))
    decision = response_data(client.post("/decisions", json={
        "company_id": company["id"],
        "decision_type": "Hold",
        "rationale": "Maintain conviction while recurring revenue is verified.",
    }))
    valuation = response_data(client.post(f"/companies/{company['id']}/valuation-models", json={
        "company_id": company["id"],
        "name": "Conviction base case",
        "description": "Valuation conditioned on recurring revenue durability.",
    }))

    statements: list[str] = []

    def record_statement(*args) -> None:
        statements.append(args[2])

    engine = db_session.get_bind()
    sqlalchemy_event.listen(engine, "before_cursor_execute", record_statement)
    try:
        response = client.get("/search/evidence?q=conviction")
    finally:
        sqlalchemy_event.remove(engine, "before_cursor_execute", record_statement)
    results = response_data(response)

    assert {item["result_type"] for item in results} == {"thesis", "alert", "decision", "valuation"}
    assert next(item for item in results if item["result_type"] == "thesis")["href"] == f"/thesis-notes/{thesis['id']}"
    assert next(item for item in results if item["result_type"] == "alert")["href"] == f"/alerts/{alert['id']}"
    assert next(item for item in results if item["result_type"] == "decision")["record_id"] == decision["id"]
    assert next(item for item in results if item["result_type"] == "valuation")["href"] == (
        f"/companies/{company['id']}/valuation/{valuation['id']}"
    )
    assert {item["claim_type"] for item in results} == {"User Assumption"}
    assert next(item for item in results if item["result_type"] == "alert")["source_name"] == "User alert"
    assert len(statements) <= SEARCH_QUERY_BUDGET
    assert response.json()["meta"]["processing_time_ms"] <= SEARCH_RESPONSE_BUDGET_MS

    thesis_only = response_data(client.get("/search/evidence?q=conviction&type=thesis"))
    assert [item["result_type"] for item in thesis_only] == ["thesis"]


def test_evidence_search_does_not_leak_owned_research_records(client):
    company = response_data(client.post("/companies", json={"ticker": "PRIV", "name": "Private Search"}))
    response_data(client.post("/thesis-notes", json={
        "company_id": company["id"],
        "title": "Private catalyst thesis",
        "thesis_text": "Private catalyst detail.",
    }))
    response_data(client.post("/alerts", json={
        "company_id": company["id"],
        "alert_type": "manual",
        "title": "Private catalyst alert",
    }))
    response_data(client.post("/decisions", json={
        "company_id": company["id"],
        "decision_type": "Pass",
        "rationale": "Private catalyst is not sufficiently supported.",
    }))
    response_data(client.post(f"/companies/{company['id']}/valuation-models", json={
        "company_id": company["id"],
        "name": "Private catalyst valuation",
    }))

    app.dependency_overrides[get_current_user] = lambda: {
        "id": "other-search-user",
        "email": "other-search@example.com",
        "name": "Other Search User",
    }
    results = response_data(client.get("/search/evidence?q=private"))

    assert not [item for item in results if item["result_type"] in {"thesis", "alert", "decision", "valuation"}]
