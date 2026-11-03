from datetime import UTC, datetime
from io import BytesIO

import pytest

from app.models import (
    Company,
    RawDocument,
    Source,
    FinancialExtractionCandidate,
    FinancialMetric,
    FinancialStatementPeriod,
    NormalizedFinancialMetric,
    NormalizedFinancialSnapshot,
    ProcessingRun,
)
from helpers import response_data


def test_reported_net_capex_does_not_request_gross_capex_backfill(db) -> None:
    from app.services.accounting_normalization import (
        FinancialReconciliationService, MetricNormalizationEngine, NormalizedSnapshotBackfillService,
    )
    from datetime import date

    company = Company(ticker="NETCAPEX", name="Mock Data net-capex coverage", currency="USD")
    db.add(company); db.flush()
    period = FinancialStatementPeriod(company_id=company.id, period_type="annual", year=2025,
        report_date=date(2025, 12, 31), currency="USD", currency_source="manual_entry", currency_confidence="high")
    db.add(period); db.flush()
    db.add_all([FinancialMetric(period_id=period.id, metric_name=code, value=value, unit="USD million")
        for code, value in (("revenue", 100), ("net_capex", 20))])
    db.commit()
    snapshot = MetricNormalizationEngine.normalize_period(db, period.id)
    assert {m.metric_code for m in snapshot.metrics} == {"revenue"}
    coverage = NormalizedSnapshotBackfillService.summarize(db, company.id)
    assert coverage["needs_backfill_count"] == 0
    reconciliation = FinancialReconciliationService.reconcile(db, company.id)
    assert reconciliation["missing_normalized_count"] == 0


def test_extract_financial_candidates_from_filing_text(client, db) -> None:
    company = Company(
        ticker="ADANIPORTS",
        name="Adani Ports and Special Economic Zone",
        market="IN",
        primary_exchange="NSE",
        local_symbol="ADANIPORTS",
        currency="INR",
        country="India",
    )
    source = Source(name="Manual Filings", source_type="manual", reliability_score=70, active=True)
    db.add_all([company, source])
    db.commit()

    document = RawDocument(
        company_id=company.id,
        source_id=source.id,
        document_type="annual_report",
        title="FY2026 Annual Report",
        url="https://example.com/adani-ports-fy2026.pdf",
        published_at=datetime(2026, 5, 31, tzinfo=UTC),
        raw_text=(
            "Revenue 12,345\n"
            "EBIT 2,100\n"
            "Net income 1,550\n"
            "Cash 4,000\n"
            "Debt 8,250\n"
            "Capex 900\n"
            "Depreciation and amortization 300\n"
            "Change in working capital 100\n"
            "Diluted shares 1,200\n"
        ),
        raw_payload_json={"source_kind": "manual_filing", "market": "IN"},
        content_hash="manual-filing:test-financial-extraction",
    )
    db.add(document)
    db.commit()

    assert client.post("/api/company-setup/start", json={"company_id": company.id}).status_code == 201

    response = client.post(f"/api/filings/{document.id}/extract-financials")

    assert response.status_code == 201
    result = response_data(response)
    assert result["raw_document_id"] == document.id
    assert result["created_count"] == 9
    metric_codes = {item["metric_code"] for item in result["candidates"]}
    assert metric_codes == {
        "revenue",
        "ebit",
        "net_income",
        "cash",
        "debt",
        "capex",
        "depreciation",
        "change_in_working_capital",
        "diluted_shares",
    }
    revenue = next(item for item in result["candidates"] if item["metric_code"] == "revenue")
    assert revenue["value"] == 12345
    assert revenue["source_text"] == "Revenue 12,345"
    assert revenue["source_line_number"] == 1
    assert revenue["source_page"] is None
    assert revenue["source_section"] is None
    assert revenue["source_locator_json"] == {
        "type": "text_line",
        "line_number": 1,
        "page": None,
        "section": None,
    }
    assert revenue["confidence_label"] == "low"
    assert "reporting_unit_missing" in revenue["extraction_warnings"]
    assert "fiscal_year_inferred_from_document" in revenue["extraction_warnings"]
    assert revenue["review_status"] == "needs_review"

    list_response = client.get(f"/api/companies/{company.id}/financial-statements/extracted")
    candidates = response_data(list_response)
    assert [item["id"] for item in candidates] == [item["id"] for item in result["candidates"]]

    setup = response_data(client.get(f"/api/company-setup/{company.id}"))
    assert setup["financial_extraction_status"] == "needs_review"
    assert setup["current_step"] == "financial_review"
    run = db.query(ProcessingRun).filter_by(
        company_id=company.id,
        run_type="filing_financial_extraction",
    ).one()
    assert run.status == "success"
    assert run.fetched_count == 9
    assert run.created_count == 9
    assert run.skipped_duplicate_count == 0


def test_extract_financial_candidates_requires_filing_text(client, db) -> None:
    company = Company(ticker="AAPL", name="Apple Inc.", market="US", primary_exchange="NASDAQ", local_symbol="AAPL")
    source = Source(name="SEC EDGAR", source_type="sec", reliability_score=95, active=True)
    db.add_all([company, source])
    db.commit()

    document = RawDocument(
        company_id=company.id,
        source_id=source.id,
        document_type="annual_report",
        title="Empty filing",
        raw_text=None,
        content_hash="empty-filing",
    )
    db.add(document)
    db.commit()

    response = client.post(f"/api/filings/{document.id}/extract-financials")

    assert response.status_code == 422
    assert "raw_text" in response.json()["detail"].lower()
    run = db.query(ProcessingRun).filter_by(
        company_id=company.id,
        run_type="filing_financial_extraction",
    ).one()
    assert run.status == "failed"
    assert run.error_count == 1


def test_extract_financial_candidates_preserves_historical_capex_and_working_capital(client, db) -> None:
    company = Company(ticker="HISTORY", name="Historical Financials Co", currency="USD")
    source = Source(name="Annual Reports", source_type="manual", reliability_score=80, active=True)
    db.add_all([company, source])
    db.flush()
    document = RawDocument(
        company_id=company.id,
        source_id=source.id,
        document_type="annual_report",
        title="FY2026 Annual Report",
        published_at=datetime(2026, 5, 31, tzinfo=UTC),
        raw_text=(
            "FY2024 Capex 700\n"
            "FY2025 Capex 800\n"
            "Capex FY2026: 900\n"
            "2024 Change in working capital 50\n"
            "2025 Change in working capital 60\n"
            "FY2026 Change in working capital 70\n"
        ),
        content_hash="manual-filing:historical-reinvestment",
    )
    db.add(document)
    db.commit()

    response = client.post(f"/api/filings/{document.id}/extract-financials")

    assert response.status_code == 201
    result = response_data(response)
    assert result["created_count"] == 6
    extracted = {
        (candidate["metric_code"], candidate["fiscal_year"]): candidate["value"]
        for candidate in result["candidates"]
    }
    assert extracted == {
        ("capex", 2024): 700,
        ("capex", 2025): 800,
        ("capex", 2026): 900,
        ("change_in_working_capital", 2024): 50,
        ("change_in_working_capital", 2025): 60,
        ("change_in_working_capital", 2026): 70,
    }

    duplicate = response_data(client.post(f"/api/filings/{document.id}/extract-financials"))
    assert duplicate["created_count"] == 0
    assert duplicate["skipped_existing_count"] == 6
    runs = db.query(ProcessingRun).filter_by(
        company_id=company.id,
        run_type="filing_financial_extraction",
    ).order_by(ProcessingRun.id).all()
    assert [run.status for run in runs] == ["success", "success"]
    assert runs[-1].skipped_duplicate_count == 6


def test_extraction_preserves_explicit_page_section_and_line_evidence(client, db) -> None:
    company = Company(ticker="EVIDENCE", name="Evidence Location Co", currency="USD")
    source = Source(name="Evidence Filings", source_type="manual", reliability_score=80, active=True)
    db.add_all([company, source])
    db.flush()
    document = RawDocument(
        company_id=company.id,
        source_id=source.id,
        document_type="annual_report",
        title="FY2026 Annual Report",
        raw_text="ITEM 8. FINANCIAL STATEMENTS\n[Page 42]\nFY2026 Revenue 1,000\n",
        content_hash="manual-filing:evidence-location",
    )
    db.add(document)
    db.commit()

    result = response_data(client.post(f"/api/filings/{document.id}/extract-financials"))

    candidate = result["candidates"][0]
    assert candidate["source_line_number"] == 3
    assert candidate["source_page"] == 42
    assert candidate["source_section"] == "ITEM 8. FINANCIAL STATEMENTS"
    assert candidate["source_locator_json"]["type"] == "text_line"
    assert candidate["source_locator_json"]["line_number"] == 3
    assert "fiscal_year_inferred_from_document" not in (candidate["extraction_warnings"] or "")

    candidate_response = client.get(f"/api/financial-line-items/{candidate['id']}")
    assert candidate_response.status_code == 200
    assert response_data(candidate_response)["raw_document_id"] == document.id


def test_candidate_requires_unit_before_review(client, db) -> None:
    company = Company(ticker="UNIT", name="Unit Review Co", currency="INR")
    source = Source(name="Unit Filings", source_type="manual", reliability_score=80, active=True)
    db.add_all([company, source])
    db.flush()
    document = RawDocument(
        company_id=company.id,
        source_id=source.id,
        document_type="annual_report",
        title="FY2026 Annual Report",
        raw_text="FY2026 Revenue 1,000",
        content_hash="manual-filing:unit-review",
    )
    db.add(document)
    db.commit()
    candidate = response_data(client.post(f"/api/filings/{document.id}/extract-financials"))["candidates"][0]

    blocked = client.patch(
        f"/api/financial-line-items/{candidate['id']}/review",
        json={"review_status": "reviewed"},
    )

    assert blocked.status_code == 422
    assert "unit" in blocked.json()["detail"].lower()
    overridden = response_data(
        client.patch(
            f"/api/financial-line-items/{candidate['id']}/override",
            json={"value": 1000, "unit": "INR crore"},
        )
    )
    assert overridden["review_status"] == "overridden"
    assert overridden["unit"] == "INR crore"


def test_review_override_and_promote_candidates_use_reviewed_unit_currency_and_filter_statuses(client, db) -> None:
    company = Company(
        ticker="ADANIPORTS",
        name="Adani Ports and Special Economic Zone",
        market="IN",
        primary_exchange="NSE",
        local_symbol="ADANIPORTS",
        currency="USD",
        country="India",
    )
    source = Source(name="Manual Filings", source_type="manual", reliability_score=70, active=True)
    db.add_all([company, source])
    db.commit()

    document = RawDocument(
        company_id=company.id,
        source_id=source.id,
        document_type="annual_report",
        title="FY2026 Annual Report",
        published_at=datetime(2026, 5, 31, tzinfo=UTC),
        raw_text="Revenue 12,345\nDebt 8,250\nCash 4,000\nDiluted shares 1,200\n",
        content_hash="manual-filing:test-financial-promotion",
    )
    db.add(document)
    db.commit()

    candidates = [
        FinancialExtractionCandidate(
            company_id=company.id,
            raw_document_id=document.id,
            metric_code="revenue",
            reported_label="Revenue",
            value=12345,
            unit="INR million",
            fiscal_year=2026,
            period_type="annual",
            source_text="Revenue 12,345",
            extraction_method="test",
            confidence_label="high",
            review_status="needs_review",
        ),
        FinancialExtractionCandidate(
            company_id=company.id,
            raw_document_id=document.id,
            metric_code="debt",
            reported_label="Debt",
            value=8250,
            unit="INR million",
            fiscal_year=2026,
            period_type="annual",
            source_text="Debt 8,250",
            extraction_method="test",
            confidence_label="high",
            review_status="needs_review",
        ),
        FinancialExtractionCandidate(
            company_id=company.id,
            raw_document_id=document.id,
            metric_code="cash",
            reported_label="Cash",
            value=4000,
            unit="INR million",
            fiscal_year=2026,
            period_type="annual",
            source_text="Cash 4,000",
            extraction_method="test",
            confidence_label="medium",
            review_status="needs_review",
        ),
    ]
    db.add_all(candidates)
    db.commit()
    for candidate in candidates:
        db.refresh(candidate)

    review_response = client.patch(
        f"/api/financial-line-items/{candidates[0].id}/review",
        json={"review_status": "reviewed"},
    )
    assert response_data(review_response)["review_status"] == "reviewed"

    override_response = client.patch(
        f"/api/financial-line-items/{candidates[1].id}/override",
        json={"value": 8400, "unit": "INR million"},
    )
    overridden = response_data(override_response)
    assert overridden["review_status"] == "overridden"
    assert overridden["value"] == 8400

    reject_response = client.patch(
        f"/api/financial-line-items/{candidates[2].id}/review",
        json={"review_status": "rejected"},
    )
    assert response_data(reject_response)["review_status"] == "rejected"

    promote_response = client.post(f"/api/companies/{company.id}/financial-statements/mark-reviewed")
    assert response_data(promote_response)["promoted_count"] == 2

    review_queue = response_data(client.get(f"/api/companies/{company.id}/financial-statements/extracted"))
    assert [(candidate["metric_code"], candidate["review_status"]) for candidate in review_queue] == [
        ("cash", "rejected")
    ]

    period = db.query(FinancialStatementPeriod).filter_by(company_id=company.id, year=2026).one()
    assert period.currency == "INR"
    assert period.currency_source == "reviewed_candidate_unit"
    assert period.currency_confidence == "high"

    metrics = {metric.metric_name: metric for metric in db.query(FinancialMetric).filter_by(period_id=period.id).all()}
    assert metrics["revenue"].value == 12345
    assert metrics["revenue"].unit == "INR million"
    assert metrics["debt"].value == 8400
    assert metrics["debt"].unit == "INR million"
    assert "cash" not in metrics

    remaining = db.query(FinancialExtractionCandidate).filter_by(company_id=company.id).all()
    assert sorted([(candidate.metric_code, candidate.review_status) for candidate in remaining]) == sorted([("cash", "rejected"), ("debt", "promoted"), ("revenue", "promoted")])


def test_promote_candidates_rejects_conflicting_reviewed_currencies(client, db) -> None:
    company = Company(ticker="FXCONFLICT", name="FX Conflict Co", currency="INR")
    source = Source(name="Reviewed Filings", source_type="manual", reliability_score=80, active=True)
    db.add_all([company, source])
    db.flush()
    document = RawDocument(
        company_id=company.id,
        source_id=source.id,
        document_type="annual_report",
        title="FY2026 Annual Report",
        raw_text="Reviewed financials",
        content_hash="manual-filing:currency-conflict",
    )
    db.add(document)
    db.flush()
    db.add_all(
        [
            FinancialExtractionCandidate(
                company_id=company.id,
                raw_document_id=document.id,
                metric_code="revenue",
                reported_label="Revenue",
                value=1000,
                unit="INR million",
                fiscal_year=2026,
                period_type="annual",
                source_text="Revenue 1000",
                review_status="reviewed",
            ),
            FinancialExtractionCandidate(
                company_id=company.id,
                raw_document_id=document.id,
                metric_code="debt",
                reported_label="Debt",
                value=100,
                unit="USD million",
                fiscal_year=2026,
                period_type="annual",
                source_text="Debt 100",
                review_status="reviewed",
            ),
        ]
    )
    db.commit()

    response = client.post(f"/api/companies/{company.id}/financial-statements/mark-reviewed")

    assert response.status_code == 422
    assert "conflicting currencies" in response.json()["detail"]
    assert db.query(FinancialStatementPeriod).filter_by(company_id=company.id).count() == 0


def test_promote_candidates_uses_exact_xbrl_period_end(client, db) -> None:
    company = Company(ticker="AAPLDATE", name="Apple Period Date", market="US", currency="USD")
    source = Source(name="SEC Period Dates", source_type="sec", reliability_score=100, active=True)
    db.add_all([company, source])
    db.flush()
    document = RawDocument(
        company_id=company.id,
        source_id=source.id,
        document_type="xbrl_facts",
        title="AAPL SEC XBRL Company Facts",
        content_hash="sec-companyfacts:promotion-date",
    )
    db.add(document)
    db.flush()
    db.add(
        FinancialExtractionCandidate(
            company_id=company.id,
            raw_document_id=document.id,
            metric_code="revenue",
            reported_label="Revenue",
            value=416_161_000_000,
            unit="USD",
            fiscal_year=2025,
            period_type="annual",
            source_text="XBRL us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
            source_locator_json={"type": "xbrl_fact", "end": "2025-09-27"},
            review_status="reviewed",
        )
    )
    db.commit()

    response = client.post(f"/api/companies/{company.id}/financial-statements/mark-reviewed")

    assert response.status_code == 200
    period = db.query(FinancialStatementPeriod).filter_by(company_id=company.id, year=2025).one()
    assert period.report_date.isoformat() == "2025-09-27"


def test_promote_candidates_rejects_conflicting_exact_period_ends(client, db) -> None:
    company = Company(ticker="DATECONFLICT", name="Date Conflict Co", market="US", currency="USD")
    source = Source(name="Date Conflict Filings", source_type="sec", reliability_score=100, active=True)
    db.add_all([company, source])
    db.flush()
    document = RawDocument(
        company_id=company.id,
        source_id=source.id,
        document_type="xbrl_facts",
        title="Conflicting period dates",
        content_hash="sec-companyfacts:promotion-date-conflict",
    )
    db.add(document)
    db.flush()
    db.add_all(
        [
            FinancialExtractionCandidate(
                company_id=company.id,
                raw_document_id=document.id,
                metric_code=metric_code,
                reported_label=metric_code,
                value=value,
                unit="USD",
                fiscal_year=2025,
                period_type="annual",
                source_text=metric_code,
                source_locator_json={"type": "xbrl_fact", "end": period_end},
                review_status="reviewed",
            )
            for metric_code, value, period_end in (
                ("revenue", 1000, "2025-09-27"),
                ("ebit", 200, "2025-09-28"),
            )
        ]
    )
    db.commit()

    response = client.post(f"/api/companies/{company.id}/financial-statements/mark-reviewed")

    assert response.status_code == 422
    assert "conflicting period-end dates" in response.json()["detail"]
    assert db.query(FinancialStatementPeriod).filter_by(company_id=company.id).count() == 0


def test_promote_candidates_records_filing_metadata_currency_confidence(client, db) -> None:
    company = Company(ticker="METAFX", name="Metadata Currency Co", currency="USD")
    source = Source(name="Reviewed Filings", source_type="manual", reliability_score=80, active=True)
    db.add_all([company, source])
    db.flush()
    document = RawDocument(
        company_id=company.id,
        source_id=source.id,
        document_type="annual_report",
        title="FY2026 Annual Report",
        raw_text="Revenue 1,000",
        raw_payload_json={"reporting_currency": "INR"},
        content_hash="manual-filing:currency-metadata",
    )
    db.add(document)
    db.flush()
    db.add(
        FinancialExtractionCandidate(
            company_id=company.id,
            raw_document_id=document.id,
            metric_code="revenue",
            reported_label="Revenue",
            value=1000,
            unit="million",
            fiscal_year=2026,
            period_type="annual",
            source_text="Revenue 1,000",
            review_status="reviewed",
        )
    )
    db.commit()

    response = client.post(f"/api/companies/{company.id}/financial-statements/mark-reviewed")

    assert response.status_code == 200
    period = db.query(FinancialStatementPeriod).filter_by(company_id=company.id, year=2026).one()
    assert period.currency == "INR"
    assert period.currency_source == "filing_metadata"
    assert period.currency_confidence == "medium"


def test_autofill_uses_promoted_financial_metrics_for_company_actuals(client, db) -> None:
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

    period = FinancialStatementPeriod(
        company_id=company.id,
        period_type="annual",
        year=2026,
        report_date=datetime(2026, 3, 31, tzinfo=UTC).date(),
        currency="INR",
    )
    db.add(period)
    db.flush()
    db.add_all(
        [
            FinancialMetric(period_id=period.id, metric_name="revenue", value=12345, unit="INR million"),
            FinancialMetric(period_id=period.id, metric_name="ebit", value=2469, unit="INR million"),
            FinancialMetric(period_id=period.id, metric_name="cash", value=4000, unit="INR million"),
            FinancialMetric(period_id=period.id, metric_name="debt", value=8250, unit="INR million"),
            FinancialMetric(period_id=period.id, metric_name="diluted_shares", value=1200, unit="million shares"),
        ]
    )
    db.commit()

    response = client.post(f"/companies/{company.id}/valuation-models/autofill", json={"base_assumptions": {}})

    assert response.status_code == 200
    draft = response_data(response)
    assumptions = draft["assumptions"]
    assert assumptions["starting_revenue"] == 12_345_000_000
    assert assumptions["cash"] == 4_000_000_000
    assert assumptions["debt"] == 8_250_000_000
    assert assumptions["diluted_shares"] == 1_200_000_000
    assert assumptions["current_operating_margin"] == pytest.approx(0.20)
    assert "provenance" in draft
    assert draft["provenance"]["starting_revenue"]["label"] == "Legacy Metrics (FY2026) (unit conversion)"
    assert draft["provenance"]["terminal_growth_rate"]["label"] == "Missing risk_free_rate"


def test_promote_candidates_creates_normalized_snapshot_for_autofill(client, db) -> None:
    company = Company(
        ticker="ADANIPORTS",
        name="Adani Ports and Special Economic Zone",
        market="IN",
        primary_exchange="NSE",
        local_symbol="ADANIPORTS",
        currency="INR",
        country="India",
    )
    source = Source(name="Manual Filings", source_type="manual", reliability_score=70, active=True)
    db.add_all([company, source])
    db.commit()

    document = RawDocument(
        company_id=company.id,
        source_id=source.id,
        document_type="annual_report",
        title="FY2026 Annual Report",
        published_at=datetime(2026, 5, 31, tzinfo=UTC),
        raw_text="Reviewed financials",
        content_hash="manual-filing:test-normalized-promotion",
    )
    db.add(document)
    db.commit()

    reviewed_candidates = [
        FinancialExtractionCandidate(
            company_id=company.id,
            raw_document_id=document.id,
            metric_code=metric_code,
            reported_label=metric_code,
            value=value,
            unit="INR million",
            fiscal_year=2026,
            period_type="annual",
            source_text=f"{metric_code} {value}",
            extraction_method="test",
            confidence_label="high",
            review_status="reviewed",
        )
        for metric_code, value in {
            "revenue": 12345,
            "ebit": 2469,
            "net_income": 1500,
            "cash": 4000,
            "debt": 8250,
            "diluted_shares": 1200,
            "capex": 900,
            "depreciation": 300,
            "change_in_working_capital": 100,
        }.items()
    ]
    db.add_all(reviewed_candidates)
    db.commit()

    promote_response = client.post(f"/api/companies/{company.id}/financial-statements/mark-reviewed")

    assert response_data(promote_response)["promoted_count"] == 9
    snapshot = db.query(NormalizedFinancialSnapshot).filter_by(company_id=company.id).one()
    normalized = {
        metric.metric_code: metric
        for metric in db.query(NormalizedFinancialMetric).filter_by(snapshot_id=snapshot.id).all()
    }
    assert normalized["revenue"].value == 12345
    assert normalized["ebit"].value == 2469
    assert normalized["net_debt"].value == 4250
    assert "nopat" not in normalized  # No reported tax basis.
    assert normalized["cash"].value == 4000
    assert normalized["debt"].value == 8250
    assert normalized["diluted_shares"].value == 1200
    assert normalized["capex"].value == 900
    assert normalized["depreciation"].value == 300
    assert normalized["change_in_nwc"].value == 100
    assert "reinvestment" not in normalized  # Acquisition coverage is missing.
    assert normalized["cash"].unit == "INR million"
    assert normalized["revenue"].provenance_notes


def test_autofill_prefers_latest_normalized_metrics_when_available(client, db) -> None:
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

    period = FinancialStatementPeriod(
        company_id=company.id,
        period_type="annual",
        year=2026,
        report_date=datetime(2026, 3, 31, tzinfo=UTC).date(),
        currency="INR",
    )
    db.add(period)
    db.flush()
    db.add_all(
        [
            FinancialMetric(period_id=period.id, metric_name="revenue", value=1000, unit="INR million"),
            FinancialMetric(period_id=period.id, metric_name="ebit", value=100, unit="INR million"),
            FinancialMetric(period_id=period.id, metric_name="cash", value=10, unit="INR million"),
            FinancialMetric(period_id=period.id, metric_name="debt", value=20, unit="INR million"),
            FinancialMetric(period_id=period.id, metric_name="diluted_shares", value=30, unit="million shares"),
        ]
    )
    snapshot = NormalizedFinancialSnapshot(company_id=company.id, period_id=period.id)
    db.add(snapshot)
    db.flush()
    db.add_all(
        [
            NormalizedFinancialMetric(snapshot_id=snapshot.id, metric_code="revenue", value=12345, unit="INR million"),
            NormalizedFinancialMetric(snapshot_id=snapshot.id, metric_code="ebit", value=2469, unit="INR million"),
            NormalizedFinancialMetric(snapshot_id=snapshot.id, metric_code="cash", value=4000, unit="INR million"),
            NormalizedFinancialMetric(snapshot_id=snapshot.id, metric_code="debt", value=8250, unit="INR million"),
            NormalizedFinancialMetric(snapshot_id=snapshot.id, metric_code="diluted_shares", value=1200, unit="million shares"),
            NormalizedFinancialMetric(snapshot_id=snapshot.id, metric_code="basic_shares", value=1180, unit="million shares"),
            NormalizedFinancialMetric(snapshot_id=snapshot.id, metric_code="minority_interests", value=45, unit="INR million"),
            NormalizedFinancialMetric(snapshot_id=snapshot.id, metric_code="preferred_stock", value=12, unit="INR million"),
            NormalizedFinancialMetric(snapshot_id=snapshot.id, metric_code="employee_options_value", value=18, unit="INR million"),
        ]
    )
    db.commit()

    response = client.post(f"/companies/{company.id}/valuation-models/autofill", json={"base_assumptions": {}})

    draft = response_data(response)
    assumptions = draft["assumptions"]
    assert assumptions["starting_revenue"] == 12_345_000_000
    assert assumptions["cash"] == 4_000_000_000
    assert assumptions["debt"] == 8_250_000_000
    assert assumptions["diluted_shares"] == 1_200_000_000
    assert assumptions["basic_shares"] == 1_180_000_000
    assert assumptions["minority_interests"] == 45_000_000
    assert assumptions["preferred_stock"] == 12_000_000
    assert assumptions["employee_options_value"] == 18_000_000
    assert assumptions["current_operating_margin"] == pytest.approx(0.20)
    assert "provenance" in draft
    assert draft["provenance"]["starting_revenue"]["label"] == "Normalized Financials (FY2026) (unit conversion)"
    assert draft["provenance"]["terminal_growth_rate"]["label"] == "Missing risk_free_rate"

def test_promote_candidates_with_missing_fields_generates_warnings(client, db) -> None:
    company = Company(
        ticker="ADANIPORTS2",
        name="Adani Ports Missing Fields",
        market="IN",
        primary_exchange="NSE",
        local_symbol="ADANIPORTS2",
        currency="INR",
        country="India",
    )
    source = Source(name="Manual Filings", source_type="manual", reliability_score=70, active=True)
    db.add_all([company, source])
    db.commit()

    document = RawDocument(
        company_id=company.id,
        source_id=source.id,
        document_type="annual_report",
        title="FY2026 Annual Report",
        published_at=datetime(2026, 5, 31, tzinfo=UTC),
        raw_text="Reviewed financials with missing fields",
        content_hash="manual-filing:test-normalized-promotion-missing",
    )
    db.add(document)
    db.commit()

    # Only provide revenue and ebit, missing others like capex, da, current assets
    reviewed_candidates = [
        FinancialExtractionCandidate(
            company_id=company.id,
            raw_document_id=document.id,
            metric_code=metric_code,
            reported_label=metric_code,
            value=value,
            unit="INR million",
            fiscal_year=2026,
            period_type="annual",
            source_text=f"{metric_code} {value}",
            extraction_method="test",
            confidence_label="high",
            review_status="reviewed",
        )
        for metric_code, value in {
            "revenue": 12345,
            "ebit": 2469,
        }.items()
    ]
    db.add_all(reviewed_candidates)
    db.commit()

    promote_response = client.post(f"/api/companies/{company.id}/financial-statements/mark-reviewed")

    assert response_data(promote_response)["promoted_count"] == 2
    snapshot = db.query(NormalizedFinancialSnapshot).filter_by(company_id=company.id).one()
    normalized = {
        metric.metric_code: metric
        for metric in db.query(NormalizedFinancialMetric).filter_by(snapshot_id=snapshot.id).all()
    }

    # Missing source inputs do not become numerical company facts.
    assert not {
        "working_capital", "reinvestment", "effective_tax_rate", "invested_capital",
        "nopat", "fcff", "fcfe", "roic", "roe", "ebitda",
    }.intersection(normalized)
    assert normalized["revenue"].value == 12345
    assert normalized["ebit"].value == 2469


def test_promote_candidates_preserves_source_provenance_for_reported_and_derived_metrics(client, db) -> None:
    from app.services.accounting_normalization import MetricNormalizationEngine

    company = Company(
        ticker="PROVENANCE",
        name="Promotion Provenance Co",
        market="IN",
        primary_exchange="NSE",
        local_symbol="PROVENANCE",
        currency="INR",
        country="India",
    )
    source = Source(name="Reviewed Annual Reports", source_type="manual", reliability_score=80, active=True)
    db.add_all([company, source])
    db.commit()

    document = RawDocument(
        company_id=company.id,
        source_id=source.id,
        document_type="annual_report",
        title="FY2026 Annual Report",
        published_at=datetime(2026, 5, 31, tzinfo=UTC),
        raw_text="Revenue 1,000\nEBIT 200\nTax expense 40\nPre-tax income 160\n",
        content_hash="manual-filing:test-normalized-provenance",
    )
    db.add(document)
    db.flush()

    candidates = [
        FinancialExtractionCandidate(
            company_id=company.id,
            raw_document_id=document.id,
            metric_code=metric_code,
            reported_label=metric_code,
            value=value,
            unit="INR million",
            fiscal_year=2026,
            period_type="annual",
            source_text=source_text,
            extraction_method="reviewed_test_source",
            confidence_label="high",
            review_status="reviewed",
        )
        for metric_code, value, source_text in (
            ("revenue", 1000, "Revenue 1,000"),
            ("ebit", 200, "EBIT 200"),
            ("tax_expense", 40, "Tax expense 40"),
            ("pre_tax_income", 160, "Pre-tax income 160"),
        )
    ]
    db.add_all(candidates)
    db.commit()

    response = client.post(f"/api/companies/{company.id}/financial-statements/mark-reviewed")

    assert response_data(response)["promoted_count"] == 4
    snapshot = db.query(NormalizedFinancialSnapshot).filter_by(company_id=company.id).one()
    normalized = {
        metric.metric_code: metric
        for metric in db.query(NormalizedFinancialMetric).filter_by(snapshot_id=snapshot.id).all()
    }
    assert "revenue: reviewed_test_source ('Revenue 1,000')" in normalized["revenue"].provenance_notes
    assert "ebit: reviewed_test_source ('EBIT 200')" in normalized["nopat"].provenance_notes
    assert "tax_expense: reviewed_test_source ('Tax expense 40')" in normalized["nopat"].provenance_notes
    assert normalized["effective_tax_rate"].value == pytest.approx(0.25)
    assert normalized["effective_tax_rate"].warnings is None

    # A reviewed restatement has not been applied yet. It cannot relabel the
    # current fact merely because its candidate happens to be returned last.
    next_document = RawDocument(
        company_id=company.id, source_id=source.id, document_type="annual_report",
        title="FY2026 restatement", raw_text="Restated revenue 2,000",
        content_hash="manual-filing:test-normalized-restatement",
    )
    db.add(next_document)
    db.flush()
    restatement = FinancialExtractionCandidate(
        company_id=company.id, raw_document_id=next_document.id,
        metric_code="revenue", reported_label="Revenue", value=2000,
        unit="INR million", fiscal_year=2026, period_type="annual",
        source_text="Restated revenue 2,000", extraction_method="restatement_source",
        review_status="reviewed", confidence_label="high",
        source_locator_json={"reviewed_basis": "Revised annual comparative.",
                             "reviewed_limitations": ["Review comparability before growth calculations."]},
    )
    db.add(restatement)
    db.commit()
    MetricNormalizationEngine.normalize_period(db, snapshot.period_id)
    current = db.query(NormalizedFinancialMetric).join(NormalizedFinancialSnapshot).filter(
        NormalizedFinancialSnapshot.company_id == company.id,
        NormalizedFinancialMetric.metric_code == "revenue",
    ).one()
    assert current.value == 1000
    assert "Restated revenue" not in current.provenance_notes

    assert response_data(client.post(
        f"/api/companies/{company.id}/financial-statements/mark-reviewed"
    ))["promoted_count"] == 1
    current = db.query(NormalizedFinancialMetric).join(NormalizedFinancialSnapshot).filter(
        NormalizedFinancialSnapshot.company_id == company.id,
        NormalizedFinancialMetric.metric_code == "revenue",
    ).one()
    assert current.value == 2000
    assert "restatement_source ('Restated revenue 2,000')" in current.provenance_notes
    assert f"document {next_document.id}, candidate {restatement.id}" in current.provenance_notes
    assert "Revised annual comparative." in current.provenance_notes
    assert current.warnings == "Review comparability before growth calculations."


def test_normalized_snapshot_backfill_supports_dry_run_and_is_idempotent(client, db) -> None:
    company = Company(ticker="BACKFILL", name="Backfill Co", currency="INR")
    db.add(company)
    db.flush()
    period = FinancialStatementPeriod(
        company_id=company.id,
        period_type="annual",
        year=2024,
        report_date=datetime(2024, 12, 31, tzinfo=UTC).date(),
        currency="INR",
    )
    db.add(period)
    db.flush()
    db.add_all(
        [
            FinancialMetric(period_id=period.id, metric_name="revenue", value=1000, unit="INR million"),
            FinancialMetric(period_id=period.id, metric_name="ebit", value=200, unit="INR million"),
            FinancialMetric(period_id=period.id, metric_name="capex", value=80, unit="INR million"),
            FinancialMetric(period_id=period.id, metric_name="depreciation", value=30, unit="INR million"),
            FinancialMetric(period_id=period.id, metric_name="change_in_working_capital", value=10, unit="INR million"),
            FinancialMetric(period_id=period.id, metric_name="acquisitions", value=5, unit="INR million"),
            FinancialMetric(period_id=period.id, metric_name="basic_shares", value=50, unit="million shares"),
            FinancialMetric(period_id=period.id, metric_name="operating_leases", value=40, unit="INR million"),
            FinancialMetric(period_id=period.id, metric_name="minority_interests", value=8, unit="INR million"),
            FinancialMetric(period_id=period.id, metric_name="preferred_stock", value=3, unit="INR million"),
            FinancialMetric(period_id=period.id, metric_name="employee_options_value", value=2, unit="INR million"),
        ]
    )
    db.commit()

    dry_run = response_data(
        client.post(
            f"/api/companies/{company.id}/financial-statements/normalized/backfill",
            json={"dry_run": True},
        )
    )
    assert dry_run["eligible_count"] == 1
    assert dry_run["normalized_count"] == 0
    assert dry_run["coverage_before"]["coverage_percent"] == 0
    assert dry_run["coverage_after"] is None
    assert db.query(NormalizedFinancialSnapshot).count() == 0
    dry_run_record = db.query(ProcessingRun).filter_by(
        company_id=company.id,
        run_type="normalized_financial_backfill",
    ).one()
    assert dry_run_record.status == "success"
    assert dry_run_record.metadata_json["dry_run"] is True

    applied = response_data(
        client.post(
            f"/api/companies/{company.id}/financial-statements/normalized/backfill",
            json={"dry_run": False},
        )
    )
    assert applied["normalized_count"] == 1
    assert applied["coverage_after"]["coverage_percent"] == 100
    assert applied["coverage_after"]["needs_backfill_count"] == 0
    db.refresh(period)
    assert period.currency_source == "financial_metric_unit_backfill"
    assert period.currency_confidence == "medium"
    backfill_runs = db.query(ProcessingRun).filter_by(
        company_id=company.id,
        run_type="normalized_financial_backfill",
    ).order_by(ProcessingRun.id).all()
    assert len(backfill_runs) == 2
    assert backfill_runs[-1].created_count == 1
    assert backfill_runs[-1].metadata_json["dry_run"] is False
    snapshot = db.query(NormalizedFinancialSnapshot).filter_by(period_id=period.id).one()
    normalized_codes = {
        metric.metric_code
        for metric in db.query(NormalizedFinancialMetric).filter_by(snapshot_id=snapshot.id).all()
    }
    assert {
        "acquisitions",
        "basic_shares",
        "capex",
        "change_in_nwc",
        "depreciation",
        "employee_options_value",
        "lease_liabilities",
        "operating_leases",
        "minority_interests",
        "preferred_stock",
        "reinvestment",
    }.issubset(normalized_codes)

    second_dry_run = response_data(
        client.post(
            f"/api/companies/{company.id}/financial-statements/normalized/backfill",
            json={"dry_run": True},
        )
    )
    assert second_dry_run["eligible_count"] == 0

    coverage = response_data(
        client.get(f"/api/companies/{company.id}/financial-statements/normalized/coverage")
    )
    assert coverage["status"] == "complete"
    assert coverage["normalized_period_count"] == 1
    assert coverage["trust_ready_period_count"] == 1

    reconciliation = response_data(
        client.get(f"/api/companies/{company.id}/financial-statements/normalized/reconciliation")
    )
    assert reconciliation["status"] == "complete"
    assert reconciliation["mismatch_count"] == 0
    assert reconciliation["exact_count"] >= 11

    revenue = db.query(FinancialMetric).filter_by(period_id=period.id, metric_name="revenue").one()
    revenue.value = 1100
    db.commit()
    reconciliation = response_data(
        client.get(f"/api/companies/{company.id}/financial-statements/normalized/reconciliation")
    )
    assert reconciliation["status"] == "blocked"
    mismatch = next(
        item
        for item in reconciliation["periods"][0]["items"]
        if item["metric_code"] == "revenue"
    )
    assert mismatch["status"] == "mismatch"
    assert mismatch["source_value"] == 1100
    assert mismatch["normalized_value"] == 1000
    assert mismatch["delta"] == -100


def test_screener_upload_creates_traceable_document_and_currency_units(client, db) -> None:
    import openpyxl

    company = Company(
        ticker="SCREEN",
        name="Screener Upload Co",
        market="IN",
        primary_exchange="NSE",
        local_symbol="SCREEN",
        currency="INR",
    )
    db.add(company)
    db.commit()

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Data Sheet"
    sheet.cell(row=2, column=2, value="Mar 2026")
    sheet.cell(row=3, column=1, value="Sales")
    sheet.cell(row=3, column=2, value=1250)
    content = BytesIO()
    workbook.save(content)

    response = client.post(
        f"/api/companies/{company.id}/fundamentals/screener",
        files={
            "file": (
                "screen-export.xlsx",
                content.getvalue(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 201
    result = response_data(response)
    assert result["extracted_count"] == 1
    document = db.query(RawDocument).filter_by(company_id=company.id, document_type="screener_export").one()
    assert document.source_id is not None
    assert document.content_hash.startswith("screener-upload:")
    assert document.raw_payload_json["original_filename"] == "screen-export.xlsx"
    candidate = db.query(FinancialExtractionCandidate).filter_by(raw_document_id=document.id).one()
    assert candidate.unit == "INR crore"
    assert candidate.source_section == "Data Sheet"
    assert candidate.source_line_number == 3
    assert candidate.source_table_name == "Data Sheet"
    assert candidate.source_row_label == "Sales"
    assert candidate.source_column_label == "Mar 2026"
    assert candidate.source_cell_reference == "B3"
    assert candidate.source_locator_json == {
        "type": "spreadsheet_cell",
        "sheet": "Data Sheet",
        "row": 3,
        "column": 2,
        "cell": "B3",
        "header_row": 2,
    }
    run = db.query(ProcessingRun).filter_by(company_id=company.id, run_type="screener_upload").one()
    assert run.status == "success"
    assert run.fetched_count == 1
    assert run.created_count == 1


def test_promote_candidates_skips_reviewed_items_without_fiscal_year(client, db) -> None:
    company = Company(
        ticker="NOFY",
        name="Missing Fiscal Year Co",
        market="US",
        primary_exchange="NASDAQ",
        local_symbol="NOFY",
        currency="USD",
    )
    source = Source(name="Manual Filings", source_type="manual", reliability_score=70, active=True)
    db.add_all([company, source])
    db.commit()

    document = RawDocument(
        company_id=company.id,
        source_id=source.id,
        document_type="annual_report",
        title="Annual Report",
        raw_text="Revenue 1,000",
        content_hash="manual-filing:test-promotion-missing-year",
    )
    db.add(document)
    db.flush()
    candidate = FinancialExtractionCandidate(
        company_id=company.id,
        raw_document_id=document.id,
        metric_code="revenue",
        reported_label="Revenue",
        value=1000,
        unit="USD million",
        fiscal_year=None,
        period_type="annual",
        source_text="Revenue 1,000",
        extraction_method="test",
        confidence_label="high",
        review_status="reviewed",
    )
    db.add(candidate)
    db.commit()

    response = client.post(f"/api/companies/{company.id}/financial-statements/mark-reviewed")

    assert response_data(response)["promoted_count"] == 0
    db.refresh(candidate)
    assert candidate.review_status == "reviewed"
    assert db.query(NormalizedFinancialSnapshot).filter_by(company_id=company.id).count() == 0
