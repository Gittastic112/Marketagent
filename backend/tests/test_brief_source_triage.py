"""Deterministic comparison of isolated Mock Data, without AI or valuation writes."""
import json
from datetime import UTC, date, datetime
from hashlib import sha256

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from app.api.dependencies import get_current_user
from app.main import app
from app.models import AiOutput, BriefSource, Company, User
from conftest import TEST_USER_ID


@pytest.fixture
def evidence(db):
    company = Company(ticker="TRIAGE", name="Mock Data comparison", currency="USD")
    other_company = Company(ticker="OTHER", name="Mock Data other company", currency="USD")
    db.add_all([company, other_company, User(id="other-owner", email="other@example.test", name="Other")])
    db.flush()
    ids = (company.id, other_company.id)

    def add(direction="increase", *, content=None, owner=TEST_USER_ID, company_id=None,
            mock=False, review="pending", field="starting_revenue", status="complete", archived=False):
        # Non-mock flags below exercise gates, not a claim that fixture content is genuine.
        text = content or f"Mock Data report number {len(db.new)} {direction} {datetime.now(UTC).isoformat()} discusses revenue."
        digest = sha256(text.encode()).hexdigest()
        source = BriefSource(user_id=owner, company_id=company_id or ids[0], title="Mock Data source",
            source_kind="text", source_sha256=digest, identity_hash=sha256((text + review + field).encode()).hexdigest(),
            content_text=text, extraction_json={"text_sha256": digest, "character_count": len(text), "warnings": []},
            as_of_date=date(2024, 1, 2), analysis_status=status,
            archived_at=datetime.now(UTC) if archived else None)
        db.add(source)
        db.flush()
        marker = f"brief_source:{source.id}"
        analysis = {"source_marker": f"[source_id:{marker}]", "summary": "Mock Data findings for comparison testing.",
            "findings": [{"title": "Mock Data revenue finding", "importance": "high",
                "importance_reason": "Review the revenue assumptions against this source.", "quote": text,
                "confidence": "low", "valuation_inputs": [{"field": field, "direction": direction,
                    "reason": "Review this hypothesis against the source and forecast basis."}]}]}
        output = AiOutput(user_id=owner, reference_type="brief_source", reference_id=source.id,
            provider_name="fixture", model_name="fixture-model", prompt_version="brief-source-v2", input_hash=digest,
            source_ids_json=[marker], output_text=json.dumps(analysis), confidence_label="low", is_mock=mock,
            human_review_status=review, citation_validation_status="valid",
            citations_json=[{"source_id": marker, "status": "valid", "quote": text, "start_char": 0, "end_char": len(text)}])
        db.add(output)
        db.flush()
        source.ai_output_id = output.id
        source.analysis_json = analysis
        db.commit()
        return source, output

    return ids, add


def triage(client, company_id, **params):
    response = client.get("/brief-sources/triage", params={"company_id": company_id, **params})
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "private, no-store"
    body = response.json()
    assert body["errors"] == []
    assert body["meta"]["source"] == "stored_private_source_comparison"
    return body["data"]


def test_compares_only_same_company_and_owner_with_exact_provenance(client, db, evidence):
    (company_id, other_id), add = evidence
    first, _ = add()
    second, _ = add("decrease")
    add("decrease", owner="other-owner")
    add("decrease", company_id=other_id)
    result = triage(client, company_id)
    assert {source["id"] for source in result["sources"]} == {first.id, second.id}
    group = result["groups"][0]
    assert group["status"] == "opposing_directions"
    assert group["source_count"] == group["distinct_content_count"] == 2
    assert group["review_href"] == f"/companies/{company_id}/valuation/draft#starting_revenue"
    assert len(group["items"]) == 2
    assert result["coverage"]["active_sources"] == 2
    assert result["claim_type"] == "Calculation"
    for source in result["sources"]:
        assert source["prompt_version"] and source["input_hash"] and source["source_sha256"]
        assert source["generated_at"] and source["as_of_date"] and source["review_status"] == "pending"
        assert source["findings"][0]["start_char"] == 0
        assert not {"content_text", "pdf_bytes", "user_id", "output_text"}.intersection(source)
    app.dependency_overrides[get_current_user] = lambda: {"id": "other-owner"}
    assert len(triage(client, company_id)["sources"]) == 1


def test_missing_unknown_dates_and_same_direction_never_claim_agreement(client, db, evidence):
    (company_id, _), add = evidence
    source, _ = add()
    source.as_of_date = None
    add(field="revenue_growth_years_json")
    db.commit()
    result = triage(client, company_id)
    assert all(group["status"] == "no_opposition_detected" for group in result["groups"])
    assert any("unknown" in warning.lower() for source in result["sources"] for warning in source["warnings"])
    assert result["groups"][1]["review_href"].endswith("#revenue-growth")
    assert any("not" in warning and "contradiction" in warning for warning in result["warnings"])


def test_exact_text_duplicates_do_not_create_cross_source_opposition(client, evidence):
    (company_id, _), add = evidence
    text = "Mock Data identical original text copied into separate dated source records."
    add(content=text)
    add("decrease", content=text, review="approved")
    group = triage(client, company_id)["groups"][0]
    assert group["source_count"] == 2 and group["distinct_content_count"] == 1
    assert group["status"] == "mixed_within_content"


def test_mock_and_real_flagged_records_never_create_cross_basis_conflicts(client, evidence):
    (company_id, _), add = evidence
    add()
    add("decrease", mock=True)
    result = triage(client, company_id)
    assert len(result["sources"]) == 1 and result["coverage"]["excluded"]["mock"] == 1
    included = triage(client, company_id, include_mock=True)
    assert len(included["sources"]) == 2 and included["groups"][0]["status"] == "no_opposition_detected"
    add("increase", mock=True)
    assert triage(client, company_id, include_mock=True)["groups"][0]["status"] == "opposing_directions"


@pytest.mark.parametrize("status", ["not_scanned", "scanning", "failed"])
def test_incomplete_scans_are_explicit_coverage_gaps(client, evidence, status):
    (company_id, _), add = evidence
    add(status=status)
    result = triage(client, company_id)
    assert not result["sources"] and not result["groups"]
    assert result["coverage"]["excluded"][status] == 1


@pytest.mark.parametrize("review", ["rejected", "needs_revision", "unknown_status"])
def test_unusable_review_states_do_not_resurface_as_suggestions(client, evidence, review):
    (company_id, _), add = evidence
    add(review=review)
    result = triage(client, company_id)
    assert not result["sources"]
    assert result["coverage"]["excluded"].get(review, result["coverage"]["excluded"].get("unusable")) == 1


@pytest.mark.parametrize("corruption", ["owner", "reference", "marker", "blocked", "failed", "citation_status",
    "quote", "offset", "invalid_json", "invalid_field", "recommendation", "malformed_receipt"])
def test_unverified_or_mismatched_outputs_fail_closed(client, db, evidence, corruption):
    (company_id, _), add = evidence
    source, output = add()
    if corruption == "owner": output.user_id = "other-owner"
    elif corruption == "reference": output.reference_id = source.id + 100
    elif corruption == "marker": output.source_ids_json = ["brief_source:999"]
    elif corruption == "blocked": output.is_blocked = True
    elif corruption == "failed": output.execution_status = "failed"
    elif corruption == "citation_status": output.citation_validation_status = "partial"
    elif corruption == "quote": output.citations_json = [{**output.citations_json[0], "quote": "Invented unrelated quotation"}]
    elif corruption == "offset": output.citations_json = [{**output.citations_json[0], "end_char": 999999}]
    elif corruption == "invalid_json": output.output_text = "invalid JSON"
    elif corruption == "invalid_field": output.output_text = output.output_text.replace("starting_revenue", "unregistered_input")
    elif corruption == "malformed_receipt": output.citations_json = ["Not a citation receipt"]
    else: output.output_text = output.output_text.replace("Mock Data findings", "You should buy this stock")
    db.commit()
    result = triage(client, company_id)
    assert not result["sources"] and result["coverage"]["excluded"]["unusable"] == 1


def test_review_only_and_unmapped_findings_remain_visible_without_direction_inference(client, db, evidence):
    (company_id, _), add = evidence
    add("review")
    _, output = add()
    analysis = json.loads(output.output_text)
    analysis["findings"][0]["valuation_inputs"] = []
    output.output_text = json.dumps(analysis)
    db.commit()
    result = triage(client, company_id)
    assert len(result["sources"]) == 2
    assert result["unmapped_findings"] == [{"source_id": output.reference_id, "finding_index": 0}]
    assert result["groups"][0]["status"] == "no_opposition_detected"


def test_stored_display_links_cannot_override_canonical_draft_targets(client, db, evidence):
    (company_id, _), add = evidence
    source, _ = add()
    source.analysis_json = {"findings": [{"valuation_inputs": [{"review_href": "javascript:alert(1)", "label": "Untrusted label"}]}]}
    db.commit()
    result = triage(client, company_id)
    assert result["groups"][0]["review_href"] == f"/companies/{company_id}/valuation/draft#starting_revenue"
    assert "javascript" not in json.dumps(result) and "Untrusted label" not in json.dumps(result)


def test_archiving_and_review_changes_recompute_the_comparison(client, db, evidence):
    (company_id, _), add = evidence
    source, _ = add()
    _, output = add("decrease")
    assert triage(client, company_id)["groups"][0]["status"] == "opposing_directions"
    output.human_review_status = "rejected"
    db.commit()
    assert triage(client, company_id)["groups"][0]["status"] == "no_opposition_detected"
    source.archived_at = datetime.now(UTC)
    db.commit()
    result = triage(client, company_id)
    assert result["sources"] == [] and result["coverage"]["archived_sources"] == 1


def test_read_has_bounded_rows_no_body_loads_or_writes_and_discloses_truncation(client, db, evidence):
    (company_id, _), add = evidence
    for _ in range(52): add()
    db.expunge_all()
    statements, loaded = [], []
    def record(_conn, _cursor, statement, *_args): statements.append(statement)
    def on_load(source, _context): loaded.append(source.id)
    engine = db.get_bind()
    event.listen(engine, "before_cursor_execute", record)
    event.listen(BriefSource, "load", on_load)
    try: result = triage(client, company_id)
    finally:
        event.remove(engine, "before_cursor_execute", record)
        event.remove(BriefSource, "load", on_load)
    assert len(statements) <= 4 and len(loaded) == 50  # One bounded latest-review query, no receipt bodies.
    assert all(statement.lstrip().upper().startswith("SELECT") for statement in statements)
    assert all("content_text" not in statement.lower().split("from")[0] and "pdf_bytes" not in statement.lower().split("from")[0] for statement in statements)
    assert result["coverage"]["not_examined"] == 2 and result["coverage"]["examined_sources"] == 50
    assert any("50" in warning and "older" in warning for warning in result["warnings"])


def test_empty_missing_and_invalid_company_and_authentication(client, evidence):
    (company_id, _), _ = evidence
    assert triage(client, company_id)["groups"] == []
    assert client.get("/brief-sources/triage", params={"company_id": 99999}).status_code == 404
    for params in ({}, {"company_id": 0}, {"company_id": "abc"}, {"company_id": company_id, "include_mock": "perhaps"}):
        assert client.get("/brief-sources/triage", params=params).status_code == 422
    override = app.dependency_overrides.pop(get_current_user)
    try:
        with TestClient(app) as anonymous:
            assert anonymous.get("/brief-sources/triage", params={"company_id": company_id}).status_code == 401
    finally: app.dependency_overrides[get_current_user] = override
