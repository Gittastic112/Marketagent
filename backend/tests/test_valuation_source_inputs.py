from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.models import Company, FinancialExtractionCandidate, RawDocument, Source
from app.models.macro import MacroObservation, MacroSeries
from app.models.market_price import MarketPrice
from app.services.assumption_autofill_engine import AssumptionAutofillEngine
from app.services.valuation_source_inputs import sec_draft_inputs, stored_usd_risk_free_rate, stored_market_price
from app.services.valuation_setup_draft import ValuationSetupDraftService


def company_and_candidates(db):
    company = Company(ticker="INPUT", name="Mock Data issuer", market="US", currency="USD")
    source = Source(name="SEC test fixture", source_type="sec")
    db.add_all([company, source])
    db.flush()
    document = RawDocument(company_id=company.id, source_id=source.id,
        title="Mock Data SEC payload", document_type="xbrl_facts", content_hash="mock-sec-inputs")
    db.add(document)
    db.flush()
    for metric, value in {"revenue": 1000, "ebit": 200, "cash": 100, "current_debt": 25,
        "long_term_debt_noncurrent": 75, "book_equity": 500, "diluted_shares": 20,
        "capex": 60, "depreciation": 25, "dividends": 10, "new_debt_issued": 0}.items():
        db.add(FinancialExtractionCandidate(company_id=company.id, raw_document_id=document.id,
            metric_code=metric, reported_label=metric, value=value,
            unit="shares" if metric == "diluted_shares" else "USD", fiscal_year=2025,
            period_type="annual", source_text="Mock Data", extraction_method="sec_xbrl_v3",
            source_locator_json={"end": "2025-12-31", "accession": "mock-annual",
                "source_url": "https://data.sec.gov/api/xbrl/companyfacts/CIK0000000001.json"}))
    db.commit()
    return company


def add_rate(db, *, units="%", currency_date=None):
    series = MacroSeries(name="DGS10", provider_name="FRED", units=units, frequency="D",
        source_url="https://fred.stlouisfed.org/series/DGS10")
    db.add(series)
    db.flush()
    observation = MacroObservation(series_id=series.id, value=4.5, date_recorded=currency_date or date.today())
    db.add(observation)
    db.commit()
    return observation


def test_fred_uses_exact_observation_percent_conversion_and_usd_only(db_session):
    row = add_rate(db_session)
    value, source = stored_usd_risk_free_rate(db_session, "USD")
    assert value == 0.045
    assert source["source_record_id"] == row.id
    assert source["requires_review"] is True
    assert source["claim_type"] == "Estimate"
    assert stored_usd_risk_free_rate(db_session, "INR") is None


@pytest.mark.parametrize("units,offset", [("Index", 0), ("%", 1)])
def test_fred_refuses_wrong_units_and_future_observation(db_session, units, offset):
    add_rate(db_session, units=units, currency_date=date.today() + timedelta(days=offset))
    assert stored_usd_risk_free_rate(db_session, "USD") is None


def test_candidates_populate_draft_without_promoting_facts_or_missing_zeros(db_session):
    company = company_and_candidates(db_session)
    inputs = sec_draft_inputs(db_session, company)
    assert inputs["debt"][0] == 100
    assert inputs["invested_capital"][0] == 500
    assert inputs["operating_margin"][0] == 0.2
    assert inputs["new_debt_issued"][0] == 0
    assert "employee_options_value" not in inputs
    assert "debt_repaid" not in inputs
    draft = ValuationSetupDraftService.create_or_reopen(db_session, company.id, "test-owner")
    assert draft.assumptions_json["starting_revenue"] == 1000
    assert draft.assumptions_json["capex"] == 60
    assert draft.provenance_json["starting_revenue"]["claim_type"] == "Source Summary"
    assert "starting_revenue" in draft.source_metadata_json["review_fields"]
    assert draft.status == "draft"
    assert all(row.review_status == "needs_review" for row in db_session.query(FinancialExtractionCandidate))


def test_rejected_latest_candidate_does_not_reenter_draft(db_session):
    company = company_and_candidates(db_session)
    row = db_session.query(FinancialExtractionCandidate).filter_by(metric_code="revenue").one()
    row.review_status = "rejected"
    db_session.commit()
    assert "revenue" not in sec_draft_inputs(db_session, company)


def test_existing_v2_annual_values_remain_usable_but_long_term_only_debt_does_not(db_session):
    company = company_and_candidates(db_session)
    revenue = db_session.query(FinancialExtractionCandidate).filter_by(metric_code="revenue").one()
    revenue.extraction_method = "sec_xbrl_v2"
    current_debt = db_session.query(FinancialExtractionCandidate).filter_by(metric_code="current_debt").one()
    current_debt.metric_code = "debt"
    current_debt.extraction_method = "sec_xbrl_v2"
    db_session.commit()
    result = sec_draft_inputs(db_session, company)
    assert result["revenue"][0] == 1000
    assert "debt" not in result


def test_different_filing_bases_are_not_summed(db_session):
    company = company_and_candidates(db_session)
    row = db_session.query(FinancialExtractionCandidate).filter_by(metric_code="current_debt").one()
    row.source_locator_json = {**row.source_locator_json, "accession": "another-filing"}
    db_session.commit()
    assert "debt" not in sec_draft_inputs(db_session, company)


def test_current_price_is_available_without_financial_history_and_not_redated(db_session):
    company = Company(name="Mock Data company", ticker="PRICE", currency="USD", market="US")
    db_session.add(company)
    db_session.flush()
    row = MarketPrice(company_id=company.id, ticker=company.ticker, price=Decimal("123.45"),
        as_of_date=date.today() - timedelta(days=8), provider_name="manual", currency="USD")
    db_session.add(row)
    db_session.commit()
    result = AssumptionAutofillEngine.draft_assumptions(db_session, company.id)
    assert result["assumptions"]["current_market_price"] == 123.45
    assert result["provenance"]["current_market_price"]["is_stale"] is True
    row.claim_type = "Mock Data"
    db_session.commit()
    assert stored_market_price(db_session, company) is None


def test_fred_refresh_preserves_user_edits_and_invalidates_rate_review(db_session):
    company = company_and_candidates(db_session)
    rate = add_rate(db_session)
    draft = ValuationSetupDraftService.create_or_reopen(db_session, company.id, "owner")
    assert draft.assumptions_json["risk_free_rate"] == 0.045
    draft = ValuationSetupDraftService.update(db_session, draft, {"starting_revenue": 1200},
        ["starting_revenue", "risk_free_rate"])
    rate.value = 5.0
    db_session.commit()
    draft = ValuationSetupDraftService.create_or_reopen(db_session, company.id, "owner")
    assert draft.assumptions_json["starting_revenue"] == 1200
    assert draft.assumptions_json["risk_free_rate"] == 0.05
    assert "starting_revenue" in draft.reviewed_fields_json
    assert "risk_free_rate" not in draft.reviewed_fields_json


@pytest.mark.parametrize("provider,price_type,claim", [
    ("e2e_mock_fixture", "close", "Fact"),
    ("manual", "Mock Data", "Fact"),
    ("demo_provider", "close", "Fact"),
    ("manual", "close", "mock data"),
])
def test_mock_quote_markers_cannot_become_real_draft_prices(db_session, provider, price_type, claim):
    company = company_and_candidates(db_session)
    db_session.add(MarketPrice(company_id=company.id, ticker=company.ticker,
        price=100, currency="USD", as_of_date=date.today(), provider_name=provider,
        price_type=price_type, claim_type=claim))
    db_session.commit()
    assert stored_market_price(db_session, company) is None


def test_daily_age_increment_preserves_review_until_source_becomes_stale(db_session, monkeypatch):
    from app.services import valuation_source_inputs
    company = company_and_candidates(db_session)
    add_rate(db_session)
    draft = ValuationSetupDraftService.create_or_reopen(db_session, company.id, "owner")
    draft = ValuationSetupDraftService.update(db_session, draft, {}, ["risk_free_rate"])
    initial_date = date.today()

    class TestDate(date):
        offset = 1

        @classmethod
        def today(cls):
            return initial_date + timedelta(days=cls.offset)

    monkeypatch.setattr(valuation_source_inputs, "date", TestDate)
    draft = ValuationSetupDraftService.create_or_reopen(db_session, company.id, "owner")
    assert draft.provenance_json["risk_free_rate"]["age_days"] == 1
    assert "risk_free_rate" in draft.reviewed_fields_json
    TestDate.offset = 8
    draft = ValuationSetupDraftService.create_or_reopen(db_session, company.id, "owner")
    assert draft.provenance_json["risk_free_rate"]["is_stale"] is True
    assert "risk_free_rate" not in draft.reviewed_fields_json


def test_reviewed_million_scale_is_not_mixed_with_absolute_sec_candidates(db_session):
    from app.models.financial import FinancialStatementPeriod, FinancialMetric
    company = company_and_candidates(db_session)
    period = FinancialStatementPeriod(company_id=company.id, year=2025, period_type="annual",
        report_date=date(2025, 12, 31), currency="USD")
    db_session.add(period)
    db_session.flush()
    db_session.add(FinancialMetric(period_id=period.id, metric_name="revenue", value=2, unit="USD million"))
    db_session.commit()
    result = AssumptionAutofillEngine.draft_assumptions(db_session, company.id)
    assert result["assumptions"]["starting_revenue"] == 2_000_000
    assert result["provenance"]["starting_revenue"]["original_value"] == 2
    assert result["assumptions"]["capex"] is None


def test_reviewed_sec_components_normalize_without_partial_debt_or_unit_mixing(db_session):
    from app.models.financial import FinancialStatementPeriod, FinancialMetric, NormalizedFinancialMetric
    from app.services.accounting_normalization import MetricNormalizationEngine
    company = company_and_candidates(db_session)
    period = FinancialStatementPeriod(company_id=company.id, year=2025, period_type="annual",
        report_date=date(2025, 12, 31), currency="USD")
    db_session.add(period)
    db_session.flush()
    first = FinancialMetric(period_id=period.id, metric_name="current_debt", value=20, unit="USD")
    second = FinancialMetric(period_id=period.id, metric_name="long_term_debt_noncurrent", value=80, unit="USD")
    db_session.add_all([first, second])
    db_session.commit()
    snapshot = MetricNormalizationEngine.normalize_period(db_session, period.id)
    assert db_session.query(NormalizedFinancialMetric).filter_by(snapshot_id=snapshot.id, metric_code="debt").one().value == 100
    second.unit = "USD million"
    db_session.commit()
    snapshot = MetricNormalizationEngine.normalize_period(db_session, period.id)
    assert db_session.query(NormalizedFinancialMetric).filter_by(snapshot_id=snapshot.id, metric_code="debt").first() is None
