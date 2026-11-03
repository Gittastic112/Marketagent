"""Mock Data only: comparison semantics, owner isolation and immutable brief evidence."""
from copy import deepcopy
from datetime import UTC, date, datetime, time, timedelta
import json

import pytest
from sqlalchemy import event, select

from app.models import DailyBrief
from app.models.brief_review import BriefComparisonReview
from app.schemas.brief import DailyBriefPayload
from app.schemas.brief_sources import BriefAnalysis
from app.schemas.brief_triage import BriefReviewWrite
from app.services.brief_comparison_reviews import review_detail, save_review
from app.services.brief_private_context import snapshot_private_research
from app.services.brief_source_triage import compare_sources
from app.services.daily_brief_schedule import configure_daily_brief_schedule, run_due_daily_brief_schedules
from app.services.morning_briefing_engine import MorningBriefingEngine
from conftest import TEST_USER_ID
from test_brief_source_triage import evidence


def context_labels(output, period="FY2025", currency="USD", scope="consolidated"):
    payload = json.loads(output.output_text)
    payload["findings"][0]["valuation_inputs"][0]["comparison_context"] = {
        "period": period, "currency": currency, "economic_scope": scope}
    output.output_text = json.dumps(payload)


def receipt_for(db, company_id):
    comparison = compare_sources(db, TEST_USER_ID, company_id)
    return save_review(db, TEST_USER_ID, BriefReviewWrite(company_id=company_id, field="starting_revenue",
        evidence_hash=comparison.evidence_hash, expected_version=0, disposition="investigate",
        notes="Mock Data: inspect the forecast horizon before changing any input.", evidence_reviewed=True))


@pytest.mark.parametrize("dimension,label", [("period", "FY2026"), ("currency", "EUR"), ("economic_scope", "segment")])
def test_incompatible_quoted_context_is_explicit_without_inferred_contradiction(db, evidence, dimension, label):
    (company_id, _), add = evidence
    _, first = add(content="Mock Data FY2025 USD consolidated revenue has an increase hypothesis.")
    labels = {"period": "FY2025", "currency": "USD", "scope": "consolidated"}
    labels["scope" if dimension == "economic_scope" else dimension] = label
    _, second = add("decrease", content=f"Mock Data {labels['period']} {labels['currency']} {labels['scope']} revenue has a decrease hypothesis.")
    context_labels(first)
    context_labels(second, **labels)
    db.commit()
    result = compare_sources(db, TEST_USER_ID, company_id)
    assert result.methodology == "private-source-direction-comparison-v2"
    assert result.groups[0].comparability_status == "incompatible"
    assert result.groups[0].comparability[dimension].status == "incompatible"
    assert result.groups[0].status == "opposing_directions"
    assert any("not a verified contradiction" in warning for warning in result.warnings)


def test_unknown_context_is_not_inferred_from_source_date_and_unquoted_labels_fail(db, evidence):
    (company_id, _), add = evidence
    _, first = add(content="Mock Data FY2025 USD consolidated revenue will be reviewed.")
    add("decrease")
    context_labels(first)
    db.commit()
    result = compare_sources(db, TEST_USER_ID, company_id)
    assert result.groups[0].comparability_status == "unknown"
    context_labels(first, period="FY2099")
    with pytest.raises(ValueError, match="literal text"):
        BriefAnalysis.model_validate_json(first.output_text)


def test_current_receipts_and_pending_sources_have_separate_owned_queues(db, evidence):
    (company_id, other_company_id), add = evidence
    first, output = add(review="approved", content="Mock Data FY2025 USD consolidated revenue requires a careful review.")
    second, output2 = add("decrease", review="approved", content="Mock Data FY2025 USD consolidated revenue is a different review hypothesis.")
    context_labels(output)
    context_labels(output2)
    db.commit()
    review = receipt_for(db, company_id)
    pending, _ = add(company_id=other_company_id)
    foreign, _ = add(owner="other-owner")
    add(mock=True, company_id=other_company_id)
    add(review="rejected", company_id=other_company_id)
    context = snapshot_private_research(db, TEST_USER_ID, date.today())
    assert {item["source"]["id"] for item in context["sources"]} == {first.id, second.id, pending.id}
    assert foreign.id not in {item["source"]["id"] for item in context["sources"]}
    assert context["reviewed"][0]["receipt"]["id"] == review.id
    assert context["reviewed"][0]["comparability_status"] == "same"
    assert context["reviewed"][0]["receipt"]["claim_type"] == "User Assumption"
    assert context["review_queue"][0]["state"] == "pending_ai_review"
    assert context["excluded"]["mock"] == context["excluded"]["rejected"] == 1
    assert all(item["freshness"] == "historical" for item in context["sources"])


def test_old_receipts_become_stale_without_rewriting_stored_evidence(db, evidence):
    (company_id, _), add = evidence
    add(review="approved")
    receipt = receipt_for(db, company_id)
    row = db.get(BriefComparisonReview, receipt.id)
    row.evidence_hash = "a" * 64
    row.evidence_json = {**row.evidence_json, "methodology": "private-source-direction-comparison-v1"}
    db.commit()
    before = deepcopy(row.evidence_json)
    context = snapshot_private_research(db, TEST_USER_ID, date.today())
    assert context["reviewed"] == []
    assert context["review_queue"][0]["state"] == "stale_receipt"
    assert review_detail(db, TEST_USER_ID, row.id).evidence.methodology.endswith("v1")
    assert row.evidence_json == before


def test_copied_sources_remain_exclusions_and_reads_are_bounded(db, evidence):
    (company_id, _), add = evidence
    text = "Mock Data same source copied into two independent-looking records."
    add(content=text)
    add("decrease", content=text, review="approved")
    statements = []
    def record(_connection, _cursor, statement, *_args):
        statements.append(statement)
    db.expunge_all()
    event.listen(db.get_bind(), "before_cursor_execute", record)
    try:
        context = snapshot_private_research(db, TEST_USER_ID, date.today())
    finally:
        event.remove(db.get_bind(), "before_cursor_execute", record)
    assert len(statements) == 6
    assert all("content_text" not in statement and "pdf_bytes" not in statement and "evidence_json" not in statement for statement in statements)
    assert context["excluded"]["duplicate_content"] == 1
    assert len(context["sources"]) == 1
    assert context["reviewed"] == []
    assert not db.new and not db.dirty and not db.deleted


def test_manual_and_due_briefs_keep_as_generated_private_context_without_ai(db, evidence, monkeypatch):
    (_, _), add = evidence
    source, _ = add()
    def forbidden(*_args, **_kwargs):
        raise AssertionError("Deterministic brief must not invoke external AI")
    monkeypatch.setattr("app.services.morning_briefing_engine.detect_thesis_contradiction", forbidden)
    monkeypatch.setattr("app.services.morning_briefing_engine.map_event_to_dcf_variables", forbidden)
    now = datetime.now(UTC)
    schedule = configure_daily_brief_schedule(db, user_id=TEST_USER_ID, enabled=True, timezone_name="UTC",
        local_time=time(7), days_of_week=list(range(7)), now=now - timedelta(days=1))
    schedule.next_run_at = now - timedelta(seconds=1)
    db.commit()
    result = run_due_daily_brief_schedules(db, user_id=TEST_USER_ID, now=now)
    assert result["briefs_created"] == 1
    saved = db.scalar(select(DailyBrief).where(DailyBrief.user_id == TEST_USER_ID))
    snapshot = deepcopy(saved.payload_json)
    assert snapshot["private_research"]["sources"][0]["source"]["id"] == source.id
    source.archived_at = now
    db.commit()
    assert MorningBriefingEngine.get_or_generate_briefing(db, TEST_USER_ID, now.date()).payload_json == snapshot
    manual = MorningBriefingEngine.generate_briefing(db, TEST_USER_ID, now.date(), allow_generation=False)
    assert manual.payload_json["private_research"]["sources"] == []
    assert saved.payload_json == snapshot
    assert DailyBriefPayload.model_validate({"summary": "Old saved brief"}).private_research is None


def test_snapshot_limits_and_future_evidence_do_not_claim_complete_coverage(db, evidence, monkeypatch):
    (_, _), add = evidence
    add()
    add("decrease")
    monkeypatch.setattr("app.services.brief_private_context.SOURCE_LIMIT", 1)
    context = snapshot_private_research(db, TEST_USER_ID, date.today())
    assert len(context["sources"]) == 1
    assert context["status"] == "partial"
    assert context["excluded"]["sources_outside_snapshot_limit"] == 1
    assert snapshot_private_research(db, TEST_USER_ID, date.today() - timedelta(days=1))["sources"] == []
