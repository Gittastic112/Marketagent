from datetime import date

from app.models.company import Company
from app.services.sec_ingestion import SecFilingMetadata
from helpers import response_data
import pytest


def test_us_filing_discovery_returns_sec_candidates(client, db, monkeypatch) -> None:
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

    def fake_preview(cik: str, form_types: tuple[str, ...], filing_year: int | None, limit: int) -> list[SecFilingMetadata]:
        assert cik == "0000320193"
        assert form_types == ("10-K",)
        assert filing_year == 2026
        assert limit == 5
        return [
            SecFilingMetadata(
                accession_number="0000320193-26-000001",
                form_type="10-K",
                filing_date=date(2026, 10, 30),
                report_date=date(2026, 9, 30),
                primary_document="aapl-20260930.htm",
                filing_url="https://www.sec.gov/Archives/edgar/data/320193/000032019326000001/aapl-20260930.htm",
            )
        ]

    monkeypatch.setattr("app.providers.filings.sec_edgar.fetch_recent_sec_filing_metadata", fake_preview)

    response = client.get(f"/api/companies/{company.id}/filings/discover?form_type=10-K&filing_year=2026&limit=5")

    assert response.status_code == 200
    data = response_data(response)
    assert data["company_id"] == company.id
    assert data["provider_name"] == "SEC EDGAR"
    assert data["mode"] == "automated"
    assert data["manual_required"] is False
    assert data["filings"][0]["accession_number"] == "0000320193-26-000001"


def test_india_filing_discovery_is_manual_only(client, db) -> None:
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

    response = client.get(f"/api/companies/{company.id}/filings/discover")

    assert response.status_code == 200
    data = response_data(response)
    assert data["provider_name"] == "India Manual Filings"
    assert data["mode"] == "manual"
    assert data["manual_required"] is True
    assert data["filings"] == []
    assert "manual" in data["next_action"].lower()
    assert data["official_manual_source"] is None


@pytest.mark.parametrize("ticker,isin,host", [
    ("RELIANCE", "INE002A01018", "www.ril.com"),
    ("HDFCBANK", "INE040A01034", "www.hdfc.bank.in"),
    ("BHARTIARTL", "INE397D01024", "www.airtel.in"),
    ("ICICIBANK", "INE090A01021", "www.icici.bank.in"),
    ("SBIN", "INE062A01020", "sbi.bank.in"),
])
def test_scoped_india_sources_have_dated_official_identity_links(client, db, ticker, isin, host):
    from urllib.parse import urlsplit
    company = Company(ticker=ticker, local_symbol=ticker, name="Mock Data identity fixture",
        market="IN", primary_exchange="NSE", currency="INR", isin=isin)
    db.add(company)
    db.commit()
    data = response_data(client.get(f"/api/companies/{company.id}/filings/discover"))
    source = data["official_manual_source"]
    assert source["security_isin"] == isin
    assert source["checked_on"] == "2026-10-12"
    assert urlsplit(source["url"]).hostname == host
    assert source["target_years"] == [2024, 2025, 2026]
    assert source["required_documents"]
    assert data["manual_required"] and data["filings"] == []
    company.isin = "UNVERIFIED"
    db.commit()
    assert response_data(client.get(f"/api/companies/{company.id}/filings/discover"))["official_manual_source"] is None


def test_manual_filing_link_creates_traceable_document_and_updates_setup(client, db) -> None:
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

    assert client.post("/api/company-setup/start", json={"company_id": company.id}).status_code == 201

    create_response = client.post(
        f"/api/companies/{company.id}/filings/manual-link",
        json={
            "document_type": "annual_report",
            "title": "FY2026 Annual Report",
            "url": "https://example.com/adani-ports-fy2026.pdf",
            "published_at": "2026-05-31T00:00:00Z",
            "raw_text": "Revenue and port volume disclosure",
        },
    )

    assert create_response.status_code == 201
    document = response_data(create_response)
    assert document["company_id"] == company.id
    assert document["document_type"] == "annual_report"
    assert document["raw_payload_json"]["source_kind"] == "manual_filing"
    assert document["raw_payload_json"]["market"] == "IN"

    list_response = client.get(f"/api/companies/{company.id}/filings")
    filings = response_data(list_response)
    assert [filing["id"] for filing in filings] == [document["id"]]

    filing_response = client.get(f"/api/filings/{document['id']}")
    assert response_data(filing_response)["title"] == "FY2026 Annual Report"

    setup = response_data(client.get(f"/api/company-setup/{company.id}"))
    assert setup["filing_status"] == "needs_review"
    assert setup["current_step"] == "financial_extraction"
