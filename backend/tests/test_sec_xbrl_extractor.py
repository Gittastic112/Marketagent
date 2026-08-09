import pytest
from sqlalchemy.orm import Session
from app.models import Company, FinancialExtractionCandidate, ProcessingRun, RawDocument, Source
from app.services.sec_xbrl_extractor import extract_xbrl_candidates

def mock_http_get(*args, **kwargs):
    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "cik": 320193,
                "entityName": "Apple Inc.",
                "facts": {
                    "us-gaap": {
                        "Revenues": {
                            "label": "Revenues",
                            "units": {
                                "EUR": [
                                    {"end": "2023-09-30", "val": 999, "fy": 2023, "form": "10-K", "frame": "CY2023"}
                                ],
                                "USD": [
                                    {
                                        "start": "2021-09-26", "end": "2022-09-24",
                                        "val": 394328000000, "fy": 2022, "fp": "FY", "form": "10-K",
                                        "filed": "2022-10-28", "accn": "0000320193-22-000108", "frame": None,
                                    },
                                    {
                                        "start": "2021-09-26", "end": "2022-09-24",
                                        "val": 394328000000, "fy": 2023, "fp": "FY", "form": "10-K",
                                        "filed": "2023-11-03", "accn": "0000320193-23-000106", "frame": "CY2022",
                                    },
                                    {
                                        "start": "2022-09-25", "end": "2023-09-30",
                                        "val": 383285000000, "fy": 2023, "fp": "FY", "form": "10-K",
                                        "filed": "2023-11-03", "accn": "0000320193-23-000106", "frame": "CY2023",
                                    },
                                ]
                            }
                        },
                        "NetIncomeLoss": {
                            "label": "Net Income (Loss)",
                            "units": {
                                "USD": [
                                    {
                                        "start": "2022-09-25", "end": "2023-09-30",
                                        "val": 96995000000, "fy": 2023, "fp": "FY", "form": "10-K",
                                        "filed": "2023-11-03", "accn": "0000320193-23-000106", "frame": "CY2023",
                                    }
                                ]
                            }
                        }
                    }
                }
            }

    return MockResponse()

def test_extract_xbrl_candidates(db_session: Session):
    # Setup company
    company = Company(
        name="Apple Inc.",
        ticker="AAPL",
        cik="320193",
        market="US"
    )
    db_session.add(company)
    db_session.commit()

    # Run extractor
    result = extract_xbrl_candidates(
        db=db_session,
        company_id=company.id,
        http_get=mock_http_get,
        user_agent="Tester test@example.com"
    )

    # AAPL 2023 Rev, 2022 Rev, 2023 NetIncome -> 3 candidates
    assert result["created_count"] == 3
    assert result["selected_fiscal_years"] == [2022, 2023]
    # Gaps must be reported for each year, not hidden by aggregate coverage.
    assert len(result["warnings"]) == 1
    assert result["missing_core_metrics_by_year"] == {
        "2022": ["cash", "debt", "diluted_shares", "ebit", "net_income"],
        "2023": ["cash", "debt", "diluted_shares", "ebit"],
    }
    assert "Missing critical metrics by fiscal year" in result["warnings"][0]

    candidates = db_session.query(FinancialExtractionCandidate).filter_by(company_id=company.id).all()
    assert len(candidates) == 3

    rev_2023 = next((c for c in candidates if c.metric_code == "revenue" and c.fiscal_year == 2023), None)
    assert rev_2023 is not None
    assert rev_2023.value == 383285000000
    assert rev_2023.extraction_method == "sec_xbrl_v2"
    assert rev_2023.source_row_label == "Revenues"
    assert rev_2023.source_column_label == "FY2023"
    assert rev_2023.source_locator_json["type"] == "xbrl_fact"
    assert rev_2023.source_locator_json["concept"] == "Revenues"
    assert rev_2023.source_locator_json["fiscal_year"] == 2023
    assert rev_2023.source_locator_json["end"] == "2023-09-30"
    assert rev_2023.source_locator_json["accession"] == "0000320193-23-000106"
    assert rev_2023.source_locator_json["payload_sha256"]
    assert rev_2023.source_locator_json["source_url"].endswith("CIK0000320193.json")

    fallback_doc = db_session.query(RawDocument).filter_by(
        company_id=company.id,
        document_type="xbrl_facts",
    ).one()
    assert fallback_doc.url == rev_2023.source_locator_json["source_url"]
    assert fallback_doc.content_hash.startswith("sec-companyfacts:")
    assert fallback_doc.raw_payload_json["payload_sha256"] == rev_2023.source_locator_json["payload_sha256"]
    assert fallback_doc.raw_payload_json["companyfacts"]["entityName"] == "Apple Inc."

    net_inc_2023 = next((c for c in candidates if c.metric_code == "net_income" and c.fiscal_year == 2023), None)
    assert net_inc_2023 is not None
    assert net_inc_2023.value == 96995000000


def test_extract_xbrl_fallback_document_uses_sec_source_not_first_source(db_session: Session):
    unrelated_source = Source(name="Manual Research", source_type="manual", reliability_score=50)
    company = Company(
        name="Apple Inc.",
        ticker="AAPL",
        cik="320193",
        market="US"
    )
    db_session.add_all([unrelated_source, company])
    db_session.commit()

    result = extract_xbrl_candidates(
        db=db_session,
        company_id=company.id,
        http_get=mock_http_get,
        user_agent="Tester test@example.com"
    )

    assert result["created_count"] == 3
    fallback_doc = db_session.query(RawDocument).filter_by(
        company_id=company.id,
        document_type="xbrl_facts",
    ).one()
    assert fallback_doc.source_id != unrelated_source.id
    assert fallback_doc.source.name == "SEC EDGAR"
    assert fallback_doc.source.source_type == "sec"

def test_extract_xbrl_endpoint_success(client, db_session: Session, monkeypatch):
    company = Company(
        name="Apple Inc.",
        ticker="AAPL",
        cik="320193",
        market="US"
    )
    db_session.add(company)
    db_session.commit()

    # Mock the http fetcher
    monkeypatch.setattr("app.services.sec_xbrl_extractor.httpx.get", mock_http_get)

    response = client.post(f"/api/companies/{company.id}/extract-xbrl")
    assert response.status_code == 201

    data = response.json()
    assert data["meta"]["status"] == "success"
    assert data["data"]["created_count"] == 3
    assert data["data"]["selected_fiscal_years"] == [2022, 2023]
    assert data["data"]["missing_core_metrics_by_year"]["2022"]
    assert len(data["meta"]["warnings"]) == 1
    assert "Missing critical metrics by fiscal year" in data["meta"]["warnings"][0]
    run = db_session.query(ProcessingRun).filter_by(
        company_id=company.id,
        run_type="sec_xbrl_extraction",
    ).one()
    assert run.status == "success"
    assert run.fetched_count == 3
    assert run.created_count == 3
    assert run.metadata_json["missing_core_metrics_by_year"]["2022"]

def test_extract_xbrl_endpoint_missing_cik(client, db_session: Session):
    company = Company(
        name="No CIK Inc.",
        ticker="NOCIK",
        market="US"
    )
    db_session.add(company)
    db_session.commit()

    response = client.post(f"/api/companies/{company.id}/extract-xbrl")
    assert response.status_code == 400
    assert response.json()["detail"] == "Company has no CIK configured"
    run = db_session.query(ProcessingRun).filter_by(
        company_id=company.id,
        run_type="sec_xbrl_extraction",
    ).one()
    assert run.status == "failed"
