"""Mock Data financial-review planning, isolated from the normal database."""
from datetime import UTC, date, datetime

from sqlalchemy import func, select

from app.models.company import Company
from app.models.financial import FinancialMetric, FinancialStatementPeriod, FinancialExtractionCandidate, NormalizedFinancialSnapshot
from app.models.source import Source
from app.models.raw_document import RawDocument
from app.models.source_fact_revision import SourceFactRevision
from app.services.financial_review_plan import build_financial_review_plan


def company(db):
    row = Company(ticker="PLANMOCK", name="Mock Data review company", currency="INR", market="IN")
    db.add(row); db.commit()
    return row


def period(db, owner, year=2025):
    row = FinancialStatementPeriod(company_id=owner.id, year=year, period_type="annual",
        report_date=date(year, 3, 31), currency="INR", currency_source="reviewed_source_unit", currency_confidence="high")
    db.add(row); db.commit()
    return row


def field(report, metric, index=0):
    return next(row for row in report["periods"][index]["fields"] if row["metric"] == metric)


def test_empty_company_does_not_get_fabricated_periods(client, db_session):
    owner = company(db_session)
    report = client.get(f"/api/companies/{owner.id}/financial-statements/review-plan").json()["data"]
    assert report["periods"] == []
    assert report["latest_year"] is None
    assert report["source_document_count"] == 0
    assert report["actions"][0]["href"] == f"/companies/{owner.id}/filings"
    assert db_session.scalar(select(func.count()).select_from(FinancialStatementPeriod)) == 0


def test_consecutive_year_gaps_are_visible_and_bank_scope_excludes_fcff_debt(db_session):
    owner = company(db_session)
    period(db_session, owner, 2025); period(db_session, owner, 2023)
    report = build_financial_review_plan(db_session, owner.id, track="bank_equity", as_of=date(2026, 11, 7))
    assert [row["year"] for row in report["periods"]] == [2025, 2024, 2023]
    assert report["periods"][1]["period_id"] is None
    codes = {row["metric"] for row in report["periods"][0]["fields"]}
    assert "book_equity" in codes and "debt" not in codes and "revenue" not in codes


def test_manual_zero_remains_recorded_but_requires_source_link(db_session):
    owner = company(db_session); annual = period(db_session, owner)
    db_session.add(FinancialMetric(period_id=annual.id, metric_name="debt", value=0, unit="INR crore"))
    db_session.commit()
    report = build_financial_review_plan(db_session, owner.id)
    assert field(report, "debt")["status"] == "source_review"
    assert field(report, "cash")["status"] == "missing"


def test_review_plan_distinguishes_linked_fact_units_and_rejected_candidates(db_session):
    owner = company(db_session); annual = period(db_session, owner)
    source = Source(name="Mock Data source", source_type="manual")
    db_session.add(source); db_session.flush()
    document = RawDocument(company_id=owner.id, source_id=source.id, title="Mock Data report",
        document_type="annual_report", raw_text="Mock Data debt 0 INR crore", content_hash="fixture-only")
    db_session.add(document); db_session.flush()
    candidate = FinancialExtractionCandidate(company_id=owner.id, raw_document_id=document.id,
        metric_code="debt", reported_label="Mock Data debt", value=0, unit="INR crore", fiscal_year=2025,
        period_type="annual", source_text="Mock Data debt 0", review_status="reviewed")
    rejected = FinancialExtractionCandidate(company_id=owner.id, raw_document_id=document.id,
        metric_code="cash", reported_label="Mock Data cash", value=4, unit="INR crore", fiscal_year=2025,
        period_type="annual", source_text="Mock Data cash", review_status="rejected")
    db_session.add_all([candidate, rejected]); db_session.flush()
    db_session.add_all([
        FinancialMetric(period_id=annual.id, metric_name="debt", value=0, unit="INR crore"),
        FinancialMetric(period_id=annual.id, metric_name="revenue", value=10, unit="USD"),
        SourceFactRevision(company_id=owner.id, raw_document_id=document.id, financial_candidate_id=candidate.id,
            fact_key="debt", value=0, unit="INR crore", period_type="annual", effective_at=date(2025, 3, 31),
            observed_at=datetime.now(UTC), revision_number=1, claim_type="Fact"),
    ])
    db_session.commit()
    report = build_financial_review_plan(db_session, owner.id)
    assert field(report, "debt")["status"] == "recorded_with_source"
    assert field(report, "debt")["source_links"][0]["candidate_id"] == candidate.id
    assert field(report, "debt")["source_links"][0]["href"].endswith("/sections")
    assert field(report, "revenue")["status"] == "unit_review"
    assert field(report, "cash")["status"] == "missing"
    candidate.review_status = "needs_review"; db_session.commit()
    assert field(build_financial_review_plan(db_session, owner.id), "debt")["status"] == "source_review"

    candidate.review_status = "reviewed"
    candidate.metric_code = "capex"
    db_session.add(FinancialExtractionCandidate(company_id=owner.id, raw_document_id=document.id,
        metric_code="capex", reported_label="Mock Data competing scope", value=5, unit="INR crore", fiscal_year=2025,
        period_type="annual", source_text="Mock Data competing capex", review_status="reviewed"))
    db_session.commit()
    assert field(build_financial_review_plan(db_session, owner.id), "capex")["status"] == "ambiguous"


def test_duplicate_periods_never_select_arbitrary_financials(db_session):
    owner = company(db_session); period(db_session, owner); period(db_session, owner)
    report = build_financial_review_plan(db_session, owner.id)
    assert field(report, "revenue")["status"] == "ambiguous"
    assert report["periods"][0]["period_id"] is None


def test_financial_review_route_rejects_unknown_company_track_and_future_year(client, db_session):
    owner = company(db_session)
    path = f"/api/companies/{owner.id}/financial-statements/review-plan"
    assert client.get("/api/companies/999999/financial-statements/review-plan").status_code == 404
    assert client.get(path + "?track=guess").status_code == 422
    assert client.get(path + "?latest_year=2100").status_code == 422
    assert client.get(path + "?track=bank_equity&latest_year=2025").status_code == 200


def test_normalization_cannot_target_another_company_period(client, db_session):
    owner = company(db_session); annual = period(db_session, owner)
    other = Company(ticker="OTHERMOCK", name="Other Mock Data company")
    db_session.add(other); db_session.commit()
    response = client.post(f"/api/companies/{other.id}/financial-statements/{annual.id}/normalize")
    assert response.status_code == 404
    assert db_session.scalar(select(func.count()).select_from(NormalizedFinancialSnapshot)) == 0
