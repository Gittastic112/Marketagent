"""Manual source retries must preserve evidence and prior review state."""
from sqlalchemy import func, select
import pytest

from app.models import Company, RawDocument, ProcessingRun
from app.models.company_setup import CompanySetupWorkflow
from helpers import response_data


@pytest.fixture
def filing_company(db):
    company = Company(ticker="RELIANCE", name="Mock Data issuer", market="IN",
                      primary_exchange="NSE", local_symbol="RELIANCE", currency="INR")
    db.add(company)
    db.commit()
    return company


def test_manual_retry_preserves_document_and_review(client, db, filing_company):
    company = filing_company
    workflow = CompanySetupWorkflow(company_id=company.id)
    db.add(workflow)
    db.commit()
    url = f"/api/companies/{company.id}/filings/manual-link"
    payload = {"document_type": "annual_report", "title": "Mock Data annual report",
               "url": "https://example.com/report.pdf#page=14", "raw_text": "Revenue 100",
               "published_at": "2026-03-31T00:00:00Z", "raw_payload_json": {"page": 14}}
    first = response_data(client.post(url, json=payload))
    workflow.filing_status = "reviewed"
    workflow.current_step = "industry_mapping"
    db.commit()
    retry = {**payload, "published_at": "2026-03-31T05:30:00+05:30"}
    second = response_data(client.post(url, json=retry))
    assert second["id"] == first["id"]
    db.refresh(workflow)
    assert workflow.filing_status == "reviewed"
    assert workflow.current_step == "industry_mapping"
    assert db.scalar(select(func.count(RawDocument.id))) == 1
    revised = response_data(client.post(url, json={**payload, "raw_text": "Revenue 101"}))
    assert revised["id"] != first["id"]
    assert db.get(RawDocument, first["id"]).raw_text == "Revenue 100"
    db.refresh(workflow)
    assert workflow.filing_status == "needs_review"


@pytest.mark.parametrize("changes", [
    {"title": " "}, {"title": "x" * 501}, {"raw_text": "x" * 1_000_001},
    {"url": "javascript:alert(1)"}, {"url": "file:///etc/passwd"},
    {"url": "https://user:password@example.com/a"}, {"url": "http://127.0.0.1/a"},
    {"url": "http://[::1]/a"}, {"url": "http://localhost/a"},
    {"url": "https://example.com\\@localhost/a"},
    {"raw_payload_json": {"unbounded": "x" * 65537}},
])
def test_manual_invalid_input_leaves_no_document(client, db, filing_company, changes):
    response = client.post(f"/api/companies/{filing_company.id}/filings/manual-link", json={
        "document_type": "annual_report", "title": "Mock Data report", **changes})
    assert response.status_code == 422
    assert db.scalar(select(func.count(RawDocument.id))) == 0


def test_discovery_failure_is_audited_without_provider_detail(client, db, monkeypatch):
    company = Company(ticker="AAPL", name="Mock Data", market="US", cik="0000320193")
    db.add(company)
    db.commit()
    def fail(*args, **kwargs):
        raise RuntimeError("provider-secret-must-not-escape")
    monkeypatch.setattr("app.providers.filings.sec_edgar.fetch_recent_sec_filing_metadata", fail)
    response = client.get(f"/api/companies/{company.id}/filings/discover")
    assert response.status_code == 502
    run = db.scalar(select(ProcessingRun).where(ProcessingRun.run_type == "filing_discovery"))
    assert run.status == "failed" and run.finished_at and run.company_id == company.id
    assert "provider-secret" not in str(run.error_details_json) + response.text


@pytest.mark.parametrize("route", ["/api/companies/{id}/filings/discover", "/companies/{id}/filings/preview",
                                    "/companies/{id}/sec-filings/preview"])
def test_shared_issuer_preview_is_audited_for_each_compatibility_route(client, db, monkeypatch, route):
    company = Company(ticker="GOOGL", name="Mock Data Class A", market="US", cik=None,
                      regulatory_id="0001652044", regulatory_id_type="CIK")
    db.add(company)
    db.commit()
    def preview(cik, **kwargs):
        assert cik == "0001652044"
        return []
    monkeypatch.setattr("app.providers.filings.sec_edgar.fetch_recent_sec_filing_metadata", preview)
    monkeypatch.setattr("app.api.routers.companies.fetch_recent_sec_filing_metadata", preview)
    response = client.get(route.format(id=company.id))
    assert response.status_code == 200
    run = db.scalar(select(ProcessingRun).where(ProcessingRun.run_type == "filing_discovery"))
    assert run.status == "success" and run.finished_at
    assert run.fetched_count == run.created_count == 0
