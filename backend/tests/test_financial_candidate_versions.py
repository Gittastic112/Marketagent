"""Review only the candidate values that the analyst actually inspected."""
from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select

from app.models import Company, FinancialExtractionCandidate, FinancialMetric, RawDocument, Source
from app.models.source_fact_revision import SourceFactRevision


@pytest.fixture
def candidate(db):
    company = Company(ticker="FCVERSION", name="Mock Data financial review", currency="USD", market="US")
    source = Source(name="Mock Data financial review", source_type="manual", active=True)
    db.add_all([company, source]); db.flush()
    document = RawDocument(company_id=company.id, source_id=source.id, document_type="annual_report",
                           title="Mock Data financial review", raw_text="Revenue USD million 100",
                           content_hash="mock-financial-version", published_at=datetime(2026, 1, 31, tzinfo=UTC))
    db.add(document); db.flush()
    row = FinancialExtractionCandidate(company_id=company.id, raw_document_id=document.id, metric_code="revenue",
        reported_label="Revenue", value=100, unit="USD million", fiscal_year=2025, source_text="Revenue USD million 100",
        source_locator_json={"period_end": "2025-12-31"}, review_status="needs_review")
    db.add(row); db.commit()
    return row


@pytest.mark.parametrize("operation", ["review", "override"])
def test_stale_review_and_override_cannot_replace_changed_evidence(client, db, candidate, operation):
    previous = candidate.updated_at.isoformat()
    candidate.value = 125
    db.commit()
    payload = {"expected_updated_at": previous, "review_status": "reviewed"} if operation == "review" else {
        "expected_updated_at": previous, "value": 999, "unit": "USD million"}
    response = client.patch(f"/api/financial-line-items/{candidate.id}/{operation}", json=payload)
    assert response.status_code == 409, response.text
    db.refresh(candidate)
    assert candidate.value == 125 and candidate.review_status == "needs_review"


def test_promotion_rejects_changed_review_set_without_financial_writes(client, db, candidate):
    candidate.review_status = "reviewed"
    db.commit()
    inspected = {"id": candidate.id, "updated_at": candidate.updated_at.isoformat()}
    candidate.value = 200
    db.commit()
    response = client.post(f"/api/companies/{candidate.company_id}/financial-statements/mark-reviewed",
                           json={"expected_candidates": [inspected]})
    assert response.status_code == 409, response.text
    assert db.scalar(select(func.count()).select_from(FinancialMetric)) == 0
    db.refresh(candidate)
    assert candidate.review_status == "reviewed"


@pytest.mark.parametrize("operation", ["review", "override"])
def test_promoted_evidence_cannot_be_reopened_by_old_controls(client, db, candidate, operation):
    candidate.review_status = "promoted"
    db.commit()
    payload = {"review_status": "needs_review"} if operation == "review" else {"value": 900, "unit": "USD million"}
    response = client.patch(f"/api/financial-line-items/{candidate.id}/{operation}", json=payload)
    assert response.status_code == 409, response.text
    db.refresh(candidate)
    assert candidate.review_status == "promoted" and candidate.value == 100


def test_current_review_and_override_keep_zero_and_return_new_basis(client, db, candidate):
    response = client.patch(f"/api/financial-line-items/{candidate.id}/override", json={
        "value": 0, "unit": "USD million", "expected_updated_at": candidate.updated_at.isoformat()})
    assert response.status_code == 200, response.text
    result = response.json()["data"]
    assert result["value"] == 0 and result["review_status"] == "overridden"
    response = client.patch(f"/api/financial-line-items/{candidate.id}/review", json={
        "review_status": "needs_review", "expected_updated_at": result["updated_at"]})
    assert response.status_code == 200, response.text
    assert response.json()["data"]["value"] == 0


def repeated_candidate(db, candidate, **changes):
    candidate.review_status = "reviewed"
    fields = {name: getattr(candidate, name) for name in (
        "company_id", "raw_document_id", "metric_code", "reported_label", "value", "unit",
        "fiscal_year", "period_type", "source_text", "source_locator_json", "review_status")}
    fields.update(changes)
    duplicate = FinancialExtractionCandidate(**fields, source_page=2)
    db.add(duplicate)
    db.commit()
    return duplicate


def test_repeated_statement_and_note_values_create_one_fact_with_both_revisions(client, db, candidate):
    duplicate = repeated_candidate(db, candidate)
    response = client.post(f"/api/companies/{candidate.company_id}/financial-statements/mark-reviewed", json={
        "expected_candidates": [{"id":c.id,"updated_at":c.updated_at.isoformat()} for c in (candidate, duplicate)]})
    assert response.status_code == 200, response.text
    assert response.json()["data"]["promoted_count"] == 2
    assert db.scalar(select(func.count()).select_from(FinancialMetric)) == 1
    assert db.scalar(select(func.count()).select_from(SourceFactRevision)) == 2
    revisions = db.scalars(select(SourceFactRevision).order_by(SourceFactRevision.id)).all()
    assert [r.revision_number for r in revisions] == [1, 2]
    assert revisions[0].superseded_at is not None
    assert revisions[1].superseded_at is None


@pytest.mark.parametrize("changes", [{"value":125}, {"unit":"USD billion"}])
def test_conflicting_repeated_values_block_promotion_without_financial_writes(client, db, candidate, changes):
    duplicate = repeated_candidate(db, candidate, **changes)
    response = client.post(f"/api/companies/{candidate.company_id}/financial-statements/mark-reviewed", json={
        "expected_candidates": [{"id":c.id,"updated_at":c.updated_at.isoformat()} for c in (candidate, duplicate)]})
    assert response.status_code == 409, response.text
    assert db.scalar(select(func.count()).select_from(FinancialMetric)) == 0
    assert db.scalar(select(func.count()).select_from(SourceFactRevision)) == 0
    db.refresh(candidate); db.refresh(duplicate)
    assert candidate.review_status == duplicate.review_status == "reviewed"
