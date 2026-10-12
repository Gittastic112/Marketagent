"""Mock Data exercises both public entry points without external requests."""
import asyncio
from datetime import date

import pytest

from app.models import Company, FinancialExtractionCandidate, ProcessingRun
from app.models.financial import FinancialMetric, FinancialStatementPeriod
from app.services import fundamentals, sec_xbrl_extractor


@pytest.fixture
def issuer(db, monkeypatch):
    company = Company(name="Mock issuer", ticker="MOCK", market="US", currency="USD", cik="320193")
    db.add(company)
    db.commit()
    payload = {"cik": 320193, "facts": {"us-gaap": {"Revenues": {"units": {"USD": [{
        "start": "2024-01-01", "end": "2024-12-31", "val": 100,
        "fy": 2024, "fp": "FY", "form": "10-K", "filed": "2025-02-01",
        "accn": "0000320193-25-000001", "frame": "CY2024",
    }]}}}}}
    monkeypatch.setattr(sec_xbrl_extractor, "_download_company_facts", lambda *_a: payload)
    return company


@pytest.mark.parametrize("legacy", [False, True])
def test_sec_routes_create_review_candidates_and_preserve_financials(client, db, issuer, legacy):
    period = FinancialStatementPeriod(company_id=issuer.id, year=2024, period_type="annual", currency="USD",
        report_date=date(2024, 12, 31))
    db.add(period)
    db.flush()
    metric = FinancialMetric(period_id=period.id, metric_name="Revenue", value=999, unit="USD")
    db.add(metric)
    db.commit()
    path = f"/fundamentals/ingest/{issuer.ticker}" if legacy else f"/api/companies/{issuer.id}/extract-xbrl"
    response = client.post(path)
    assert response.status_code == (200 if legacy else 201)
    assert response.json()["data"]["created_count"] == 1
    if legacy:
        assert response.json()["data"]["periods_updated"] == 0
        assert response.json()["data"]["review_required"] is True
        assert any("review" in warning.lower() for warning in response.json()["meta"]["warnings"])
    candidate = db.query(FinancialExtractionCandidate).one()
    assert candidate.review_status == "needs_review"
    assert candidate.value == 100
    assert candidate.source_locator_json["payload_sha256"]
    db.refresh(metric)
    assert metric.value == 999
    assert db.query(FinancialStatementPeriod).count() == 1
    again = client.post(path)
    assert again.json()["data"]["created_count"] == 0
    assert again.json()["data"]["skipped_existing_count"] == 1
    runs = db.query(ProcessingRun).all()
    assert len(runs) == 2 and all(run.status == "success" for run in runs)
    assert runs[0].fetched_count == 1 and runs[0].created_count == 1
    assert runs[1].skipped_duplicate_count == 1


@pytest.mark.parametrize("legacy", [False, True])
def test_sec_failure_is_audited_sanitized_and_never_success(client, db, issuer, monkeypatch, caplog, legacy):
    def fail(*_a):
        raise ValueError("private-provider-payload-should-not-leak")
    monkeypatch.setattr(sec_xbrl_extractor, "_download_company_facts", fail)
    path = f"/fundamentals/ingest/{issuer.ticker}" if legacy else f"/api/companies/{issuer.id}/extract-xbrl"
    response = client.post(path)
    assert response.status_code == 502
    run = db.query(ProcessingRun).one()
    assert run.status == "failed" and run.error_count == 1 and run.finished_at
    assert "private-provider-payload" not in response.text + caplog.text + str(run.error_details_json)
    assert db.query(FinancialExtractionCandidate).count() == 0


def test_legacy_route_uses_shared_issuer_identity(client, db, issuer):
    issuer.regulatory_id_type, issuer.regulatory_id, issuer.cik = "CIK", issuer.cik, None
    db.commit()
    assert client.post(f"/fundamentals/ingest/{issuer.ticker}").json()["data"]["created_count"] == 1


def test_legacy_fetch_uses_bounded_issuer_checked_transport(issuer, monkeypatch):
    assert asyncio.run(fundamentals.fetch_sec_company_facts("320193"))["cik"] == 320193
    monkeypatch.setattr(sec_xbrl_extractor, "_download_company_facts", lambda *_a: {"cik": 1})
    with pytest.raises(ValueError, match="different issuer"):
        asyncio.run(fundamentals.fetch_sec_company_facts("320193"))
