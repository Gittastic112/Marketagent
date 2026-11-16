from datetime import date

import pytest

from app.models import (Company, Source, RawDocument, FinancialExtractionCandidate,
                        FinancialStatementPeriod, FinancialMetric, SourceFactRevision)


def setup_review(db):
    company = Company(ticker="PERIOD", name="Mock Data period guard", currency="USD")
    source = Source(name="Mock Data filing", source_type="filing")
    db.add_all([company, source]); db.flush()
    document = RawDocument(company_id=company.id, source_id=source.id, document_type="annual_report",
        title="Mock Data period evidence", content_hash="mock-period-guard", raw_text="Mock Data")
    db.add(document); db.flush()
    periods = [FinancialStatementPeriod(company_id=company.id, period_type=kind, year=2025,
        quarter=quarter, report_date=end, currency="USD") for kind, quarter, end in [
            ("annual", None, date(2025, 12, 31)),
            ("quarterly", 1, date(2025, 3, 31)), ("quarterly", 2, date(2025, 6, 30))]]
    db.add_all(periods); db.flush()
    db.add_all([FinancialMetric(period_id=period.id, metric_name="revenue", value=100 + i, unit="USD million")
                for i, period in enumerate(periods)])
    db.commit()
    return company, document, periods


def candidate(db, company, document, **changes):
    fields = dict(company_id=company.id, raw_document_id=document.id, metric_code="revenue", reported_label="Mock Data revenue", value=200,
        unit="USD million", fiscal_year=2025, period_type="annual", source_text="Mock Data revenue",
        extraction_method="mock_period_test", confidence_label="high", review_status="reviewed",
        source_locator_json={"end": "2025-12-31", "start": "2025-01-01"})
    fields.update(changes)
    item = FinancialExtractionCandidate(**fields)
    db.add(item); db.commit()
    return item


@pytest.mark.parametrize("changes", [
    {"fiscal_year": None}, {"period_type": "unknown"}, {"period_type": "ytd"},
    {"period_type": "quarterly", "source_locator_json": {"quarter": 1, "end": "2025-03-31", "start": "2025-01-01"}},
    {"period_type": "quarterly", "source_locator_json": {"quarter": 2, "end": "2025-06-30", "start": "2025-04-01"}},
    {"source_locator_json": {}}, {"source_locator_json": {"end": "invalid"}},
    {"source_locator_json": {"end": "2025-06-30", "start": "2025-01-01", "fp": "Q2"}},
    {"source_locator_json": {"end": "2025-06-30", "start": "2025-01-01"}},
    {"source_locator_json": {"end": "2025-09-30"}},
])
def test_ambiguous_or_interim_period_never_replaces_annual_or_quarter_history(client, db, changes):
    company, document, periods = setup_review(db)
    invalid = candidate(db, company, document, **changes)
    candidate(db, company, document, metric_code="ebit", value=30)
    before = [(p.id, p.quarter, p.report_date) for p in periods]
    response = client.post(f"/api/companies/{company.id}/financial-statements/mark-reviewed")
    assert response.status_code in {409, 422}
    # A caller cannot accidentally commit partial changes after a failed batch.
    db.commit(); db.expire_all()
    assert [(p.id, p.quarter, p.report_date) for p in db.query(FinancialStatementPeriod).order_by(FinancialStatementPeriod.id)] == before
    assert [m.value for m in db.query(FinancialMetric).order_by(FinancialMetric.id)] == [100, 101, 102]
    assert db.query(SourceFactRevision).count() == 0
    assert db.get(FinancialExtractionCandidate, invalid.id).review_status == "reviewed"


def test_precise_annual_restatement_leaves_both_quarters_unchanged(client, db):
    company, document, _ = setup_review(db)
    candidate(db, company, document)
    response = client.post(f"/api/companies/{company.id}/financial-statements/mark-reviewed")
    assert response.status_code == 200
    assert response.json()["data"]["promoted_count"] == 1
    assert [m.value for m in db.query(FinancialMetric).order_by(FinancialMetric.id)] == [200, 101, 102]
    item = db.query(FinancialExtractionCandidate).one()
    basis = item.source_locator_json["promoted_period_basis"]
    assert basis["start"] == "2025-01-01" and basis["end"] == "2025-12-31"
    assert basis["duration_days"] == 365 and basis["accounting_basis"] is None


@pytest.mark.parametrize("locator", [
    {"start": "2024-12-30", "end": "2025-12-31"},
    {"start": "2025-01-01", "end": "2025-12-31", "accounting_basis": "IFRS"},
])
def test_same_end_and_value_do_not_merge_distinct_duration_or_accounting_basis(client, db, locator):
    company, document, _ = setup_review(db)
    candidate(db, company, document)
    candidate(db, company, document, source_locator_json=locator)
    assert client.post(f"/api/companies/{company.id}/financial-statements/mark-reviewed").status_code == 409
    db.commit()
    assert db.query(SourceFactRevision).count() == 0
    assert [m.value for m in db.query(FinancialMetric).order_by(FinancialMetric.id)] == [100, 101, 102]


def test_duplicate_annual_periods_are_not_arbitrarily_selected(client, db):
    company, document, _ = setup_review(db)
    db.add(FinancialStatementPeriod(company_id=company.id, period_type="annual", year=2025,
        report_date=date(2025, 12, 31), currency="USD")); db.commit()
    candidate(db, company, document)
    response = client.post(f"/api/companies/{company.id}/financial-statements/mark-reviewed")
    assert response.status_code == 409
    db.commit()
    assert [m.value for m in db.query(FinancialMetric).order_by(FinancialMetric.id)] == [100, 101, 102]


def test_period_confirmation_retains_extraction_history_and_requires_current_version(client, db):
    company, document, _ = setup_review(db)
    item = candidate(db, company, document, source_locator_json={"page": 4}, review_status="needs_review")
    payload = {"period_end": "2025-12-31", "source_note": "Mock Data page 4: year ended December 31, 2025",
               "expected_updated_at": item.updated_at.isoformat()}
    response = client.patch(f"/api/financial-line-items/{item.id}/period", json=payload)
    assert response.status_code == 200
    row = response.json()["data"]
    assert row["review_status"] == "needs_review" and row["value"] == 200
    assert row["source_locator_json"]["page"] == 4 and "end" not in row["source_locator_json"]
    review = row["source_locator_json"]["period_review"]
    assert review["end"] == "2025-12-31" and review["claim_type"] == "User Assumption"
    assert review["reviewed_by"] and review["reviewed_at"]
    assert client.patch(f"/api/financial-line-items/{item.id}/period", json=payload).status_code == 409
    payload.update(expected_updated_at=row["updated_at"], source_note="Mock Data corrected citation: page 4 annual statements")
    row = client.patch(f"/api/financial-line-items/{item.id}/period", json=payload).json()["data"]
    assert row["source_locator_json"]["period_review_history"] == [review]
    assert client.patch(f"/api/financial-line-items/{item.id}/review", json={"review_status": "reviewed",
        "expected_updated_at": row["updated_at"]}).status_code == 200
    assert client.post(f"/api/companies/{company.id}/financial-statements/mark-reviewed").status_code == 200
    assert [m.value for m in db.query(FinancialMetric).order_by(FinancialMetric.id)] == [200, 101, 102]
    db.refresh(item)
    assert client.patch(f"/api/financial-line-items/{item.id}/period", json={**payload,
        "expected_updated_at": item.updated_at.isoformat()}).status_code == 409


def test_period_confirmation_cannot_overwrite_extracted_end_or_accept_blank_evidence(client, db):
    company, document, _ = setup_review(db)
    item = candidate(db, company, document)
    payload = {"period_end": "2025-09-30", "source_note": "Mock Data source page 1",
               "expected_updated_at": item.updated_at.isoformat()}
    assert client.patch(f"/api/financial-line-items/{item.id}/period", json=payload).status_code == 409
    blank = candidate(db, company, document, source_locator_json={})
    payload.update(expected_updated_at=blank.updated_at.isoformat(), source_note=" " * 20)
    assert client.patch(f"/api/financial-line-items/{blank.id}/period", json=payload).status_code == 422


@pytest.mark.parametrize("header", ["Three months ended December 31, 2025", "Nine months ended September 30, 2025", "Quarter ended December 31, 2025"])
def test_pdf_partial_year_header_cannot_be_approved_as_annual(client, db, header):
    company, document, _ = setup_review(db)
    item = candidate(db, company, document, source_column_label=header,
        extraction_method="pdf_targeted_v6", source_locator_json={"type": "pdf_table_cell"})
    response = client.patch(f"/api/financial-line-items/{item.id}/period", json={
        "period_end": "2025-12-31", "source_note": "Mock Data: same date does not establish annual duration",
        "expected_updated_at": item.updated_at.isoformat()})
    assert response.status_code == 422
    item.source_locator_json = {"type": "pdf_table_cell", "period_review": {"end": "2025-12-31"}}
    db.commit()
    assert client.post(f"/api/companies/{company.id}/financial-statements/mark-reviewed").status_code == 422
    assert db.query(SourceFactRevision).count() == 0
    assert [m.value for m in db.query(FinancialMetric).order_by(FinancialMetric.id)] == [100, 101, 102]
