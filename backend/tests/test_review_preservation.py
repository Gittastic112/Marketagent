"""Authenticated Mock Data regressions for shared evidence and private ownership."""
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import func, select

from app.models import Company, Event, RawDocument, Source, FinancialExtractionCandidate, SourceFactRevision
from app.models.thesis_note import ThesisNote, ThesisAssumption, EventThesisImpact
from app.models.user import User
from app.models.portfolio import Portfolio, PortfolioHolding
from app.models.alert import Alert


@pytest.fixture
def evidence(db_session):
    company = Company(ticker="MOCK", name="Mock Data company")
    source = Source(name="Mock Data source", source_type="filing")
    db_session.add_all([company, source, User(id="other", email="other@example.test")])
    db_session.flush()
    document = RawDocument(company_id=company.id, source_id=source.id,
        document_type="filing", title="Mock Data source", content_hash="mock-original",
        raw_text="Mock Data original evidence", published_at=datetime(2026, 1, 1, tzinfo=UTC))
    db_session.add(document)
    db_session.commit()
    return company, document


def test_shared_event_delete_preserves_both_owners_thesis_evidence(client, db_session, evidence):
    company, _ = evidence
    event = Event(company_id=company.id, title="Mock Data event", event_type="filing", information_speed="slow")
    db_session.add(event)
    db_session.flush()
    for owner in ("admin_user_id_fallback", "other"):
        note = ThesisNote(company_id=company.id, user_id=owner, title="Mock Data thesis", thesis_text="Mock Data private research")
        db_session.add(note)
        db_session.flush()
        assumption = ThesisAssumption(thesis_note_id=note.id, description="Mock Data assumption")
        db_session.add(assumption)
        db_session.flush()
        db_session.add(EventThesisImpact(event_id=event.id, thesis_assumption_id=assumption.id,
            impact_classification="Weakens", rationale="Mock Data private reasoning"))
    db_session.commit()
    response = client.delete(f"/events/{event.id}")
    assert response.status_code == 409
    assert "private reasoning" not in response.text and "other" not in response.text
    assert db_session.scalar(select(func.count()).select_from(EventThesisImpact)) == 2
    assert db_session.scalar(select(func.count()).select_from(ThesisNote)) == 2


@pytest.mark.parametrize("patch", [
    {"published_at": "2025-01-01T00:00:00Z"}, {"raw_text": "Altered Mock Data"},
    {"content_hash": "changed"}, {"company_id": None}, {"raw_payload_json": {"filed": "2020-01-01"}},
    {"url": "https://example.test/changed"}, {"document_type": "annual_report"},
])
def test_source_defining_fields_cannot_be_rewritten(client, db_session, evidence, patch):
    _, document = evidence
    response = client.patch(f"/raw-documents/{document.id}", json=patch)
    assert response.status_code == 409
    db_session.refresh(document)
    assert document.raw_text == "Mock Data original evidence"
    assert document.content_hash == "mock-original"
    assert document.published_at.date() == date(2026, 1, 1)


def test_promoted_source_delete_preserves_revision_and_candidate(client, db_session, evidence):
    company, document = evidence
    candidate = FinancialExtractionCandidate(company_id=company.id, raw_document_id=document.id,
        metric_code="revenue", reported_label="Revenue", value=100, unit="USD", fiscal_year=2025, source_text="Mock Data", review_status="promoted")
    db_session.add(candidate)
    db_session.flush()
    revision = SourceFactRevision(company_id=company.id, raw_document_id=document.id,
        financial_candidate_id=candidate.id, fact_key="revenue", value=100, unit="USD",
        period_type="annual", effective_at=date(2025, 12, 31), observed_at=datetime.now(UTC), revision_number=1, claim_type="Fact")
    db_session.add(revision)
    db_session.commit()
    assert client.delete(f"/raw-documents/{document.id}").status_code == 409
    db_session.expire_all()
    assert db_session.get(SourceFactRevision, revision.id).value == 100
    assert db_session.get(FinancialExtractionCandidate, candidate.id).review_status == "promoted"


def test_unreferenced_event_and_document_can_still_be_deleted(client, db_session, evidence):
    _, document = evidence
    event = Event(title="Mock Data unused", event_type="filing", information_speed="slow")
    db_session.add(event)
    db_session.commit()
    assert client.delete(f"/events/{event.id}").status_code == 204
    assert client.delete(f"/raw-documents/{document.id}").status_code == 204


def test_owned_alert_filter_ignores_foreign_zero_and_duplicate_holdings(client, db_session, evidence):
    company, _ = evidence
    own = Portfolio(name="Mock Data own", user_id="admin_user_id_fallback")
    other = Portfolio(name="Mock Data foreign", user_id="other")
    db_session.add_all([own, other])
    db_session.flush()
    own_holding = PortfolioHolding(portfolio_id=own.id, company_id=company.id, ticker="MOCK", quantity=0, as_of_date=date(2026, 1, 1))
    db_session.add_all([own_holding, PortfolioHolding(portfolio_id=other.id, company_id=company.id, ticker="MOCK", quantity=7, as_of_date=date(2026, 1, 1)),
        Alert(user_id="admin_user_id_fallback", company_id=company.id, alert_type="manual", title="Mock Data alert")])
    db_session.commit()
    assert client.get("/alerts?owned_only=true").json()["data"] == []
    own_holding.quantity = 2
    second = Portfolio(name="Mock Data second owned", user_id="admin_user_id_fallback")
    db_session.add(second)
    db_session.flush()
    db_session.add(PortfolioHolding(portfolio_id=second.id, company_id=company.id, ticker="MOCK", quantity=3, as_of_date=date(2026, 1, 1)))
    db_session.commit()
    assert len(client.get("/alerts?owned_only=true").json()["data"]) == 1
