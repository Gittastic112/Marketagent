from datetime import UTC, datetime
import json

import pytest
from sqlalchemy import func, select

from app.api.dependencies import get_current_user
from app.main import app
from app.models import AiOutput, BriefComparisonReview, BriefSource
from conftest import TEST_USER_ID
from test_brief_source_triage import evidence, triage


def payload(client, company_id, **changes):
    data = triage(client, company_id, include_mock=changes.get("include_mock", False))
    return {"company_id": company_id, "field": "starting_revenue", "include_mock": False,
        "evidence_hash": data["evidence_hash"], "expected_version": 0, "disposition": "investigate",
        "notes": "Mock Data decision: reconcile the source period before considering an input change.",
        "evidence_reviewed": True, **changes}


def save(client, body):
    return client.post("/brief-sources/triage/reviews", json=body)


def test_decisions_append_exact_private_receipts_without_promoting_sources_or_inputs(client, db, evidence):
    (company_id, _), add = evidence
    source, output = add()
    add("decrease")
    before = (source.source_sha256, source.analysis_json, output.human_review_status, output.output_text)
    first_payload = payload(client, company_id)
    first = save(client, first_payload)
    assert first.status_code == 201, first.text
    record = first.json()["data"]
    assert record["version"] == 1 and record["is_current"] and record["claim_type"] == "User Assumption"
    assert first.headers["cache-control"] == "private, no-store"
    after = triage(client, company_id)
    assert after["evidence_hash"] == first_payload["evidence_hash"]
    assert after["reviews"][0] == record
    assert "evidence_json" not in json.dumps(after)
    detail = client.get(f"/brief-sources/triage/reviews/{record['id']}").json()["data"]
    assert {s["id"] for s in detail["evidence"]["sources"]} == {s["id"] for s in after["sources"]}
    assert detail["evidence"]["sources"][0]["findings"][0]["quote"] == after["sources"][0]["findings"][0]["quote"]
    second = save(client, {**first_payload, "expected_version": 1, "disposition": "keep_input", "notes": "Mock Data: keep the input pending a completed annual report."})
    assert second.status_code == 201 and second.json()["data"]["version"] == 2
    assert client.get(f"/brief-sources/triage/reviews/{record['id']}").json()["data"] == detail
    db.refresh(source); db.refresh(output)
    assert before == (source.source_sha256, source.analysis_json, output.human_review_status, output.output_text)
    assert db.scalar(select(func.count()).select_from(BriefComparisonReview)) == 2


@pytest.mark.parametrize("change", ["new_source", "archive", "restore_cycle", "rescan", "review", "quote", "source_date", "title", "mock"])
def test_changed_evidence_rejects_old_form_and_marks_receipt_historical(client, db, evidence, change):
    (company_id, _), add = evidence
    source, output = add()
    body = payload(client, company_id)
    created = save(client, body).json()["data"]
    if change == "new_source": add("decrease")
    elif change == "archive": source.archived_at = datetime.now(UTC); source.lifecycle_version += 1
    elif change == "restore_cycle": source.lifecycle_version += 2
    elif change == "rescan": source.analysis_status = "scanning"
    elif change == "review": output.human_review_status = "approved"; output.reviewed_at = datetime.now(UTC)
    elif change == "quote": output.output_text = output.output_text.replace("revenue finding", "sales finding")
    elif change == "source_date": source.as_of_date = None
    elif change == "title": source.title = "Mock Data renamed evidence"
    elif change == "mock": output.is_mock = True
    db.commit()
    rejected = save(client, {**body, "expected_version": 1})
    assert rejected.status_code == 409 and "evidence changed" in rejected.text
    current = triage(client, company_id)
    assert not current["reviews"][0]["is_current"]
    historical = client.get(f"/brief-sources/triage/reviews/{created['id']}").json()["data"]
    assert not historical["is_current"]
    assert historical["evidence"]["sources"][0]["title"] == "Mock Data source"
    assert db.scalar(select(func.count()).select_from(BriefComparisonReview)) == 1


def test_stale_review_version_cannot_overwrite_and_history_is_bounded(client, db, evidence):
    (company_id, _), add = evidence
    add()
    body = payload(client, company_id)
    first = save(client, body).json()["data"]
    assert save(client, body).status_code == 409
    second = save(client, {**body, "expected_version": 1}).json()["data"]
    query = {"company_id": company_id, "field": "starting_revenue", "limit": 1}
    history = client.get("/brief-sources/triage/reviews", params=query).json()["data"]
    assert [r["id"] for r in history] == [second["id"]]
    older = client.get("/brief-sources/triage/reviews", params={**query, "before_id": second["id"]}).json()["data"]
    assert [r["id"] for r in older] == [first["id"]]
    assert client.get("/brief-sources/triage/reviews", params={**query, "limit": 999}).status_code == 422


def test_other_owners_and_companies_cannot_read_or_reuse_receipts(client, db, evidence):
    (company_id, other_id), add = evidence
    add(); add(company_id=other_id)
    body = payload(client, company_id)
    created = save(client, body).json()["data"]
    assert save(client, {**body, "company_id": other_id}).status_code == 409
    app.dependency_overrides[get_current_user] = lambda: {"id": "other-owner"}
    assert client.get(f"/brief-sources/triage/reviews/{created['id']}").status_code == 404
    assert triage(client, company_id)["reviews"] == []
    assert client.get("/brief-sources/triage/reviews", params={"company_id": company_id, "field": body["field"]}).json()["data"] == []
    assert save(client, body).status_code == 409


def test_mock_inclusive_scope_has_separate_hash_reviews_and_versions(client, db, evidence):
    (company_id, _), add = evidence
    add(); add("decrease", mock=True)
    body = payload(client, company_id)
    assert save(client, {**body, "include_mock": True}).status_code == 409
    assert save(client, body).status_code == 201
    assert triage(client, company_id, include_mock=True)["reviews"] == []
    with_mock = save(client, payload(client, company_id, include_mock=True))
    assert with_mock.status_code == 201 and with_mock.json()["meta"]["is_mock"]
    assert len(triage(client, company_id)["reviews"]) == 1


@pytest.mark.parametrize("changes", [{"evidence_reviewed": False}, {"notes": "   "}, {"notes": "x" * 2001},
    {"disposition": "approved"}, {"field": "unknown_input"}, {"user_id": "other-owner"}, {"expected_version": -1},
    {"include_mock": "false"}, {"evidence_hash": "invalid"}])
def test_review_requires_constrained_explicit_input(client, db, evidence, changes):
    (company_id, _), add = evidence
    add()
    assert save(client, payload(client, company_id, **changes)).status_code == 422
    assert db.scalar(select(func.count()).select_from(BriefComparisonReview)) == 0


def test_no_receipt_for_absent_input_or_no_evidence(client, db, evidence):
    (company_id, _), add = evidence
    add()
    assert save(client, payload(client, company_id, field="cash")).status_code == 409
    assert db.scalar(select(func.count()).select_from(BriefComparisonReview)) == 0
