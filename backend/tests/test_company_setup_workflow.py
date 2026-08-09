from app.models.company import Company
from helpers import response_data


def test_company_setup_workflow_tracks_identity_and_source_readiness(client, db, monkeypatch) -> None:
    monkeypatch.setenv("SEC_USER_AGENT", "Market Intelligence Engine test@example.com")

    company = Company(
        ticker="AAPL",
        name="Apple Inc.",
        market="US",
        primary_exchange="NASDAQ",
        local_symbol="AAPL",
        currency="USD",
        country="United States",
        cik="0000320193",
    )
    db.add(company)
    db.commit()

    start_response = client.post("/api/company-setup/start", json={"company_id": company.id})
    assert start_response.status_code == 201
    workflow = response_data(start_response)
    assert workflow["company_id"] == company.id
    assert workflow["current_step"] == "source_setup"
    assert workflow["identity_status"] == "reviewed"
    assert workflow["source_status"] == "configured"
    assert workflow["filing_status"] == "missing"
    assert workflow["financial_extraction_status"] == "missing"
    assert workflow["valuation_readiness_status"] == "blocked"
    assert workflow["source_readiness"][0]["provider_name"] == "SEC EDGAR"
    assert workflow["source_readiness"][0]["status"] == "configured"

    patch_response = client.patch(
        f"/api/company-setup/{company.id}/step",
        json={"current_step": "filing_fetch", "filing_status": "needs_review"},
    )
    assert patch_response.status_code == 200
    patched = response_data(patch_response)
    assert patched["current_step"] == "filing_fetch"
    assert patched["filing_status"] == "needs_review"

    get_response = client.get(f"/api/company-setup/{company.id}")
    assert get_response.status_code == 200
    assert response_data(get_response)["current_step"] == "filing_fetch"


def test_company_setup_is_honest_about_manual_india_workflow(client, db) -> None:
    company = Company(
        ticker="ADANIPORTS",
        name="Adani Ports and Special Economic Zone",
        market="IN",
        primary_exchange="NSE",
        local_symbol="ADANIPORTS",
        currency="INR",
        country="India",
    )
    db.add(company)
    db.commit()

    response = client.post("/api/company-setup/start", json={"company_id": company.id})

    assert response.status_code == 201
    workflow = response_data(response)
    assert workflow["identity_status"] == "needs_review"
    assert workflow["source_status"] == "manual_only"
    assert workflow["source_readiness"][0]["provider_name"] == "India Manual Filings"
    assert workflow["source_readiness"][0]["status"] == "manual_only"
    assert "manual" in workflow["source_readiness"][0]["action_required"].lower()

    confirm_response = client.post(f"/api/company-setup/{company.id}/confirm-identity")
    assert confirm_response.status_code == 200
    confirmed = response_data(confirm_response)
    assert confirmed["identity_status"] == "reviewed"
    assert confirmed["current_step"] == "source_setup"
