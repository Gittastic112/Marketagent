from datetime import date, datetime, UTC
from types import SimpleNamespace

import pytest

from app.services.accounting_normalization import (
    _select_current_sources,
    _source_provenance,
)


def source_pair(value=46.41, **changes):
    revision = SimpleNamespace(
        id=20, company_id=8, raw_document_id=12, financial_candidate_id=100,
        fact_key="basic_eps", value=value, unit="INR/share", period_type="annual",
        effective_at=date(2025, 3, 31), superseded_at=None, revision_number=2,
    )
    candidate = SimpleNamespace(
        id=100, company_id=8, raw_document_id=12, metric_code="basic_eps",
        value=value, unit="INR/share", fiscal_year=2025, period_type="annual",
        review_status="promoted", extraction_method="pdf_text_row",
        source_text="Basic EPS 46.41", source_locator_json={},
    )
    for key, value in changes.items():
        setattr(revision, key, value)
    return revision, candidate


def selected(sources, value=46.41, unit="INR/share"):
    period = SimpleNamespace(company_id=8, year=2025, period_type="annual", report_date=date(2025, 3, 31))
    metric = SimpleNamespace(metric_name="basic_eps", value=value, unit=unit)
    return _select_current_sources(period, [metric], sources)


@pytest.mark.parametrize("reverse", [False, True])
def test_restatement_uses_current_revision_even_when_old_candidate_is_returned_last(reverse):
    old = source_pair(92.81, id=19, revision_number=1, superseded_at=datetime(2026, 10, 22, tzinfo=UTC))
    current = source_pair()
    rows = [old, current] if reverse else [current, old]
    assert selected(rows) == {"basic_eps": current}


@pytest.mark.parametrize("field,value", [
    ("company_id", 9), ("effective_at", date(2025, 12, 31)),
    ("period_type", "quarterly"), ("value", 92.81), ("unit", "USD/share"),
    ("financial_candidate_id", 101), ("raw_document_id", 13),
])
def test_revision_must_match_current_period_fact_and_candidate(field, value):
    assert selected([source_pair(**{field: value})]) == {}


@pytest.mark.parametrize("field,value", [
    ("review_status", "reviewed"), ("review_status", "overridden"),
    ("value", 92.81), ("unit", "USD/share"), ("company_id", 9),
    ("fiscal_year", 2024), ("metric_code", "diluted_eps"),
    ("period_type", "quarterly"),
])
def test_unapplied_or_mutated_candidate_cannot_supply_current_provenance(field, value):
    revision, candidate = source_pair()
    setattr(candidate, field, value)
    assert selected([(revision, candidate)]) == {}


def test_duplicate_active_revisions_and_missing_candidates_are_unavailable():
    first = source_pair()
    second = source_pair(id=21, revision_number=3)
    assert selected([first, second]) == {}
    assert selected([(first[0], None)]) == {}
    assert selected([first, (second[0], None)]) == {}


def test_explicit_zero_is_valid_and_no_revision_does_not_guess_a_source():
    pair = source_pair(0)
    assert selected([pair], value=0) == {"basic_eps": pair}
    assert selected([]) == {}


def test_provenance_retains_source_identity_and_review_limitations():
    revision, candidate = source_pair()
    candidate.source_locator_json = {
        "reviewer_type": "agent_review_under_user_delegation",
        "review_decision_id": "M05-HDFCBANK-12",
        "reviewed_basis": "FY2025 comparative adjusted for the 1:1 bonus.",
        "reviewed_limitations": ["Reported EPS differs from the direct profit/share quotient."],
    }
    notes, warnings = _source_provenance(["basic_eps"], {"basic_eps": (revision, candidate)})
    assert "basic_eps: pdf_text_row ('Basic EPS 46.41')" in notes
    assert "document 12, candidate 100, revision 20" in notes
    assert "agent_review_under_user_delegation / M05-HDFCBANK-12" in notes
    assert "FY2025 comparative adjusted" in notes
    assert warnings == ["Reported EPS differs from the direct profit/share quotient."]


def test_missing_source_is_explicit_and_malformed_review_metadata_is_ignored():
    pair = source_pair()
    pair[1].source_locator_json = {"reviewed_basis": ["bad type"], "reviewed_limitations": "bad type"}
    notes, warnings = _source_provenance(["basic_eps", "net_income"], {"basic_eps": pair})
    assert "bad type" not in notes
    assert warnings == ["Current source revision unavailable for: net_income."]
    assert warnings[0] in notes


def test_restatement_retires_every_prior_active_occurrence_and_keeps_values():
    from unittest.mock import Mock
    from app.services.source_fact_history import record_financial_fact_revision

    first, candidate = source_pair(92.81)
    second, _ = source_pair(92.81, id=21, revision_number=2)
    db = Mock()
    db.scalar.side_effect = [None, 2]
    db.scalars.return_value.all.return_value = [first, second]
    candidate.value = 46.41
    current = record_financial_fact_revision(db, candidate, effective_at=date(2025, 3, 31))
    assert first.superseded_at == second.superseded_at == current.observed_at
    assert first.value == second.value == 92.81
    assert current.value == 46.41 and current.revision_number == 3
