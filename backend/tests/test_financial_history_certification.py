from datetime import date
import hashlib
import json
from types import SimpleNamespace
from pathlib import Path

import pytest

from app.models import (
    Company,
    FinancialExtractionCandidate,
    FinancialMetric,
    FinancialStatementPeriod,
    RawDocument,
    Source,
)
from app.services.accounting_normalization import MetricNormalizationEngine
from app.services.financial_history_certification import (
    _candidate_has_exact_locator,
    build_certification_report,
    resolve_certification_manifest,
)
from app.services.evidence_integrity import build_evidence_integrity_report


METRICS = {
    "revenue": 1000,
    "ebit": 180,
    "ebitda": 220,
    "net_income": 120,
    "cash": 200,
    "debt": 300,
    "diluted_shares": 100,
    "basic_shares": 98,
    "capex": 80,
    "depreciation": 50,
    "change_in_working_capital": 10,
    "acquisitions": 5,
    "operating_leases": 40,
    "cross_holdings": 15,
    "minority_interests": 5,
    "preferred_stock": 0,
    "employee_options_value": 3,
}
CORE = {"revenue", "ebit", "net_income", "cash", "debt", "diluted_shares", "cross_holdings", "operating_leases"}


def _seed_history(db, *, market: str, ticker: str):
    company = Company(
        ticker=ticker,
        name=f"{ticker} Holdings",
        market=market,
        country="United States" if market == "US" else "India",
        currency="USD" if market == "US" else "INR",
    )
    source = Source(name=f"{ticker} exchange filing", source_type="regulatory_filing")
    db.add_all([company, source])
    db.flush()
    documents = []
    for offset, year in enumerate((2023, 2024, 2025)):
        lines = [f"{metric}: {value + offset}" for metric, value in METRICS.items() if metric in CORE]
        document = RawDocument(
            company_id=company.id,
            source_id=source.id,
            document_type="annual_report",
            title=f"{ticker} annual report {year}",
            raw_text="\n".join(lines),
            content_hash=f"{ticker}-{year}-annual-report",
        )
        db.add(document)
        db.flush()
        documents.append(document)
        period = FinancialStatementPeriod(
            company_id=company.id,
            period_type="annual",
            year=year,
            report_date=date(year, 12, 31),
            currency=company.currency,
            currency_source="reviewed_candidate_unit",
            currency_confidence="high",
        )
        db.add(period)
        db.flush()
        for metric, value in METRICS.items():
            db.add(FinancialMetric(period_id=period.id, metric_name=metric, value=value + offset, unit=company.currency))
            if metric in CORE:
                source_text = f"{metric}: {value + offset}"
                db.add(
                    FinancialExtractionCandidate(
                        company_id=company.id,
                        raw_document_id=document.id,
                        metric_code=metric,
                        reported_label=metric,
                        value=value + offset,
                        unit=company.currency,
                        fiscal_year=year,
                        period_type="annual",
                        source_text=source_text,
                        source_line_number=lines.index(source_text) + 1,
                        extraction_method="certification_test_fixture",
                        confidence_label="high",
                        review_status="reviewed",
                    )
                )
        db.flush()
        MetricNormalizationEngine.normalize_period(db, period.id, commit=False)
    db.commit()
    return company, documents


def _manifest_candidate(company, documents, *, is_mock: bool = False):
    return {
        "label": company.ticker,
        "company_id": company.id,
        "market": company.market,
        "source_document_ids": [document.id for document in documents],
        "is_mock": is_mock,
        "source_assertion": "real_primary_source",
    }


def test_certification_requires_both_markets_and_live_evidence(db):
    us_company, us_documents = _seed_history(db, market="US", ticker="ACME")
    in_company, in_documents = _seed_history(db, market="IN", ticker="INDCO")

    report = build_certification_report(
        db,
        {"candidates": [
            _manifest_candidate(us_company, us_documents),
            _manifest_candidate(in_company, in_documents),
        ]},
    )

    assert report["status"] == "passed"
    assert report["certified_markets"] == ["IN", "US"]
    assert report["certified_count"] == 2


def test_portable_certification_manifest_resolves_company_and_source_hash(db):
    company, documents = _seed_history(db, market="US", ticker="PORTABLE")
    company.primary_exchange = "NASDAQ"
    company.local_symbol = "PORTABLE"
    company.regulatory_id = "CIK-PORTABLE"
    target = documents[0]
    target.url = "https://regulator.example/portable.json"
    target.raw_payload_json = {"payload_sha256": "approved-payload-hash"}
    db.commit()

    resolved = resolve_certification_manifest(
        db,
        {
            "manifest_version": "financial-history-reference-v1",
            "candidates": [
                {
                    "label": "portable",
                    "company_selector": {
                        "market": "US",
                        "primary_exchange": "NASDAQ",
                        "local_symbol": "PORTABLE",
                        "regulatory_id": "CIK-PORTABLE",
                    },
                    "source_selectors": [
                        {
                            "url": target.url,
                            "payload_sha256": "approved-payload-hash",
                        }
                    ],
                    "is_mock": False,
                    "source_assertion": "real_primary_source",
                }
            ],
        },
    )

    assert resolved["candidates"][0]["company_id"] == company.id
    assert resolved["candidates"][0]["source_document_ids"] == [target.id]
    assert "company_selector" not in resolved["candidates"][0]


def test_certification_rejects_mock_manifest_even_when_database_checks_pass(db):
    company, documents = _seed_history(db, market="US", ticker="REJECTME")

    report = build_certification_report(
        db,
        {"candidates": [_manifest_candidate(company, documents, is_mock=True)]},
    )

    candidate = report["candidates"][0]
    assert candidate["eligible_for_certification"] is False
    assert "manifest_must_explicitly_set_is_mock_false" in candidate["failures"]
    assert report["status"] == "blocked"


def test_certification_accepts_promoted_exact_evidence(db):
    company, documents = _seed_history(db, market="US", ticker="PROMOTED")
    for candidate in db.query(FinancialExtractionCandidate).filter_by(company_id=company.id):
        candidate.review_status = "promoted"
    db.commit()

    report = build_certification_report(
        db,
        {"candidates": [_manifest_candidate(company, documents)]},
    )

    candidate = report["candidates"][0]
    assert candidate["eligible_for_certification"] is True
    assert candidate["reviewed_evidence_count"] == 24


def test_certification_blocks_applicable_statement_identity_failure(db):
    company, documents = _seed_history(db, market="IN", ticker="IDENTITYFAIL")
    for period in db.query(FinancialStatementPeriod).filter_by(company_id=company.id):
        net_income = db.query(FinancialMetric).filter_by(
            period_id=period.id,
            metric_name="net_income",
        ).one().value
        db.add_all([
            FinancialMetric(
                period_id=period.id,
                metric_name="pre_tax_income",
                value=net_income + 50,
                unit="INR",
            ),
            FinancialMetric(
                period_id=period.id,
                metric_name="tax_expense",
                value=25,
                unit="INR",
            ),
        ])
    db.commit()

    report = build_certification_report(
        db,
        {"candidates": [_manifest_candidate(company, documents)]},
    )

    candidate = report["candidates"][0]
    assert candidate["statement_identity_status"] == "failed"
    assert candidate["statement_identity_failed_count"] == 3
    assert candidate["eligible_for_certification"] is False
    assert "financial_statement_identity_failed" in candidate["failures"]


def test_data_health_reports_cross_market_financial_certification(db):
    us_company, _ = _seed_history(db, market="US", ticker="HEALTHUS")
    in_company, _ = _seed_history(db, market="IN", ticker="HEALTHIN")
    for company in (us_company, in_company):
        for candidate in db.query(FinancialExtractionCandidate).filter_by(company_id=company.id):
            candidate.review_status = "promoted"
            candidate.source_locator_json = {"end": f"{candidate.fiscal_year}-12-31"}
    db.commit()

    report = build_evidence_integrity_report(db)

    assert report["financial_certification_status"] == "passed"
    assert report["certified_markets"] == ["IN", "US"]
    assert report["certified_financial_history_count"] == 2
    assert report["checked_financial_candidates"] == 48
    assert len(report["financial_histories"]) == 2
    assert {item["statement_identity_status"] for item in report["financial_histories"]} == {
        "not_available"
    }


def test_data_health_does_not_certify_unpromoted_reviewed_evidence(db):
    company, _ = _seed_history(db, market="US", ticker="HEALTHREVIEW")
    first = db.query(FinancialExtractionCandidate).filter_by(company_id=company.id).first()
    first.review_status = "promoted"
    first.source_locator_json = {"end": f"{first.fiscal_year}-12-31"}
    db.commit()

    report = build_evidence_integrity_report(db)

    assert report["financial_certification_status"] == "blocked"
    assert report["certified_financial_history_count"] == 0


def test_certification_accepts_exact_xbrl_payload_locator(db):
    company = Company(ticker="AAPL", name="Apple Inc.", market="US", currency="USD")
    source = Source(name="SEC EDGAR", source_type="sec")
    db.add_all([company, source])
    db.flush()
    observation = {
        "start": "2022-09-25",
        "end": "2023-09-30",
        "val": 383285000000,
        "form": "10-K",
        "filed": "2023-11-03",
        "accn": "0000320193-23-000106",
    }
    document = RawDocument(
        company_id=company.id,
        source_id=source.id,
        document_type="xbrl_facts",
        title="AAPL SEC company facts",
        url="https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json",
        raw_payload_json={
            "payload_sha256": "abc123",
            "companyfacts": {
                "facts": {
                    "us-gaap": {
                        "Revenues": {"units": {"USD": [observation]}},
                    }
                }
            },
        },
        content_hash="sec-companyfacts:abc123",
    )
    db.add(document)
    db.flush()
    payload = document.raw_payload_json
    payload_hash = hashlib.sha256(json.dumps(payload["companyfacts"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    document.raw_payload_json = {**payload, "payload_sha256": payload_hash}
    candidate = FinancialExtractionCandidate(
        company_id=company.id,
        raw_document_id=document.id,
        metric_code="revenue",
        reported_label="Revenue",
        value=383285000000,
        unit="USD",
        fiscal_year=2023,
        period_type="annual",
        source_text="XBRL us-gaap:Revenues",
        source_locator_json={
            "type": "xbrl_fact",
            "namespace": "us-gaap",
            "concept": "Revenues",
            "unit": "USD",
            "payload_sha256": payload_hash,
            "source_url": "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json",
            "start": observation["start"],
            "end": observation["end"],
            "filed": observation["filed"],
            "accession": observation["accn"],
            "form": observation["form"],
        },
        extraction_method="sec_xbrl_v2",
        confidence_label="high",
        review_status="reviewed",
    )
    db.add(candidate)
    db.commit()

    assert _candidate_has_exact_locator(candidate) is True

    candidate.unit = None
    assert _candidate_has_exact_locator(candidate) is False
    candidate.unit = "INR"
    assert _candidate_has_exact_locator(candidate) is False
    candidate.unit = "USD"
    candidate.fiscal_year = 2024
    assert _candidate_has_exact_locator(candidate) is False
    candidate.fiscal_year = 2023

    # A matching stored hash string is insufficient if the retained bytes changed.
    document.raw_payload_json = {**document.raw_payload_json, "companyfacts": {}}
    assert _candidate_has_exact_locator(candidate) is False
    document.raw_payload_json = {**payload, "payload_sha256": payload_hash}

    candidate.source_locator_json = {**candidate.source_locator_json, "accession": "wrong"}
    assert _candidate_has_exact_locator(candidate) is False


@pytest.mark.parametrize("change", ["missing_unit", "page_only", "wrong_page", "bad_hash", "bad_box", "wrong_owner"])
def test_pdf_locator_cannot_pass_on_page_number_alone(change):
    content = b"Mock Data PDF bytes, geometry validation only"
    digest = hashlib.sha256(content).hexdigest()
    asset = SimpleNamespace(content=content, sha256=digest, size_bytes=len(content), page_count=2)
    document = SimpleNamespace(company_id=1, asset=asset, raw_text="Mock Data", raw_payload_json={"sha256": digest})
    locator = {"type": "pdf_table_cell", "page": 1, "coordinate_system": "pdfplumber_top_left_points",
               "page_width": 612, "page_height": 792, "cell_bbox": {"x0": 10, "top": 20, "x1": 110, "bottom": 40},
               "table": 1, "row": 2, "column": 2, "cell": "P1:T1:R2:C2"}
    candidate = SimpleNamespace(company_id=1, raw_document=document, source_page=1, unit="INR million",
        source_locator_json=locator, source_text="Revenue | FY2026 | 100", source_cell_reference="P1:T1:R2:C2")
    assert _candidate_has_exact_locator(candidate)
    if change == "missing_unit": candidate.unit = None
    if change == "page_only": candidate.source_locator_json = {}
    if change == "wrong_page": candidate.source_page = 3
    if change == "bad_hash": asset.sha256 = "0" * 64
    if change == "bad_box": locator["cell_bbox"]["x1"] = 700
    if change == "wrong_owner": candidate.company_id = 2
    assert not _candidate_has_exact_locator(candidate)


def test_stored_pdf_parser_candidates_keep_verifiable_locators():
    from app.services.pdf_financial_extraction import parse_pdf_financial_tables

    content = (Path(__file__).parent / "fixtures" / "financial_statement_table.pdf").read_bytes()
    parsed = parse_pdf_financial_tables(content)
    digest = hashlib.sha256(content).hexdigest()
    asset = SimpleNamespace(content=content, sha256=digest, size_bytes=len(content), page_count=parsed.page_count)
    document = SimpleNamespace(company_id=1, asset=asset, raw_payload_json={"sha256": digest}, raw_text="Mock Data")
    hashes = {}
    for item in parsed.candidates:
        candidate = SimpleNamespace(company_id=1, raw_document=document, source_page=item.source_page,
            unit=item.unit, source_locator_json=item.source_locator_json, source_text=item.source_text,
            source_cell_reference=item.source_cell_reference, metric_code=item.metric_code, fiscal_year=item.fiscal_year)
        assert _candidate_has_exact_locator(candidate, source_hashes=hashes)
    assert len(hashes) == 1
