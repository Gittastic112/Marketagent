import pytest
from sqlalchemy.orm import Session
from app.models import Company, FinancialExtractionCandidate, ProcessingRun, RawDocument, Source
from app.services.sec_xbrl_extractor import extract_xbrl_candidates, select_annual_facts

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
    assert rev_2023.extraction_method == "sec_xbrl_v3"
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
    monkeypatch.setattr("app.services.sec_xbrl_extractor._download_company_facts", lambda *args: mock_http_get().json())

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


def test_refresh_keeps_reviewed_evidence_and_creates_revised_candidate(db_session):
    company = Company(name="Apple", ticker="AAPL", cik="320193", market="US", currency="USD")
    db_session.add(company)
    db_session.commit()
    extract_xbrl_candidates(db_session, company.id, http_get=mock_http_get)
    original = db_session.query(FinancialExtractionCandidate).filter_by(
        company_id=company.id, metric_code="revenue", fiscal_year=2023,
    ).one()
    original.review_status = "reviewed"
    db_session.commit()

    def revised(*args, **kwargs):
        response = mock_http_get()
        data = response.json()
        observation = data["facts"]["us-gaap"]["Revenues"]["units"]["USD"][-1]
        observation.update(val=400000000000, filed="2024-11-01", accn="amended-source")
        response.json = lambda: data
        return response

    result = extract_xbrl_candidates(db_session, company.id, http_get=revised)
    assert result["created_count"] == 1
    db_session.refresh(original)
    assert original.value == 383285000000
    assert original.review_status == "reviewed"
    assert extract_xbrl_candidates(db_session, company.id, http_get=revised)["created_count"] == 0


def test_expanded_annual_concepts_do_not_label_long_term_debt_as_total():
    observation = dict(start="2024-01-01", end="2024-12-31", val=20, form="10-K", fp="FY", filed="2025-02-01")
    concepts = {
        concept: {"units": {"USD": [observation]}}
        for concept in ("DepreciationDepletionAndAmortization", "PaymentsOfDividendsCommonStock",
            "PaymentsForRepurchaseOfCommonStock", "StockholdersEquity", "LongTermDebt",
            "IncomeTaxExpenseBenefit", "AssetsCurrent", "OperatingLeaseLiabilityCurrent")
    }
    selected = select_annual_facts(concepts, "USD")
    assert {metric for metric, _ in selected} == {
        "depreciation", "dividends", "buybacks", "book_equity", "long_term_debt_total",
        "tax_expense", "current_assets", "operating_lease_current",
    }
    assert ("debt", 2024) not in selected
    assert select_annual_facts(concepts, "INR") == {}
    observation["val"] = float("nan")
    assert select_annual_facts(concepts, "USD") == {}


def test_wrong_issuer_is_rejected_before_writing(db_session):
    company = Company(name="Different issuer", ticker="WRONG", cik="1234", market="US")
    db_session.add(company)
    db_session.commit()
    with pytest.raises(ValueError, match="different issuer"):
        extract_xbrl_candidates(db_session, company.id, http_get=mock_http_get)
    assert db_session.query(FinancialExtractionCandidate).count() == 0


def test_two_share_classes_keep_separate_source_documents_for_the_same_issuer(db_session):
    first = Company(name="Issuer class one", ticker="ONE", market="US", currency="USD", cik="320193")
    second = Company(name="Issuer class two", ticker="TWO", market="US", currency="USD",
        regulatory_id="320193", regulatory_id_type="CIK")
    db_session.add_all([first, second])
    db_session.commit()
    for company in (first, second):
        assert extract_xbrl_candidates(db_session, company.id, http_get=mock_http_get)["created_count"] == 3
    documents = db_session.query(RawDocument).all()
    assert len(documents) == 2
    assert documents[0].content_hash != documents[1].content_hash
    assert {document.company_id for document in documents} == {first.id, second.id}
