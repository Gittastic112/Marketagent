"""Mock Data regressions for currency/share scale in generated valuation inputs."""
from datetime import date

import pytest

from app.models import Company, FinancialMetric, FinancialStatementPeriod
from app.models.market_price import MarketPrice
from app.services.assumption_autofill_engine import AssumptionAutofillEngine
from app.services.valuation_setup_draft import ValuationSetupDraftService


@pytest.mark.parametrize("value", [None, "", "  ", True, False, float("nan"), float("inf")])
def test_missing_or_nonfinite_amounts_cannot_be_reviewed_as_zero(value):
    assert not ValuationSetupDraftService._valid_value("cash", value)


def test_invalid_growth_values_cannot_complete_review():
    assert not ValuationSetupDraftService._valid_value("revenue_growth_years_json", {"1": float("inf")})
    assert not ValuationSetupDraftService._valid_value("revenue_growth_years_json", [True])
    assert ValuationSetupDraftService._valid_value("cash", 0)


@pytest.mark.parametrize("money_unit,money_factor,share_unit,share_factor", [
    ("INR crore", 10_000_000, "shares", 1),
    ("INR million", 1_000_000, "shares thousand", 1_000),
    ("USD million", 1_000_000, "million shares", 1_000_000),
    ("INR lakh", 100_000, "shares lakh", 100_000),
    ("USD billion", 1_000_000_000, "billion shares", 1_000_000_000),
    ("USD", 1, "shares", 1),
])
def test_generated_inputs_align_money_and_shares_without_rewriting_facts(
    db_session, money_unit, money_factor, share_unit, share_factor
):
    currency = money_unit.split()[0]
    company = Company(name="Mock Data units", ticker="UNITS", market="US", currency=currency)
    db_session.add(company)
    db_session.flush()
    period = FinancialStatementPeriod(company_id=company.id, year=date.today().year,
        period_type="annual", report_date=date.today(), currency=currency)
    db_session.add(period)
    db_session.flush()
    raw = {"revenue": 100, "ebit": 20, "cash": 0, "debt": 15, "invested_capital": 50,
        "net_income": 12, "diluted_shares": 25}
    facts = [FinancialMetric(period_id=period.id, metric_name=key, value=value,
        unit=share_unit if key == "diluted_shares" else money_unit) for key, value in raw.items()]
    db_session.add_all(facts)
    db_session.commit()

    result = AssumptionAutofillEngine.draft_assumptions(db_session, company.id)
    values = result["assumptions"]
    assert values["starting_revenue"] == 100 * money_factor
    assert values["cash"] == 0
    assert values["debt"] == 15 * money_factor
    assert values["diluted_shares"] == 25 * share_factor
    assert values["net_income"] / values["diluted_shares"] == pytest.approx(12 * money_factor / (25 * share_factor))
    assert values["current_operating_margin"] == 0.2
    assert values["sales_to_capital_ratio"] == 2
    source = result["provenance"]["diluted_shares"]
    assert source["unit"] == share_unit
    assert source["input_unit"] == "shares"
    assert source["unit_multiplier"] == share_factor
    assert source["original_value"] == 25
    assert result["source_metadata"]["input_unit_policy"] == "full_currency_and_shares_v1"
    assert [(row.value, row.unit) for row in facts] == [
        (value, share_unit if key == "diluted_shares" else money_unit) for key, value in raw.items()]


@pytest.mark.parametrize("unit", [None, "unknown", "USD crore", "INR per share", "INR million thousand"])
def test_unknown_or_wrong_currency_units_withhold_suggested_amounts(db_session, unit):
    company = Company(name="Mock Data ambiguous units", ticker="GAP", market="IN", currency="INR")
    db_session.add(company)
    db_session.flush()
    period = FinancialStatementPeriod(company_id=company.id, year=date.today().year,
        period_type="annual", report_date=date.today(), currency="INR")
    db_session.add(period)
    db_session.flush()
    db_session.add(FinancialMetric(period_id=period.id, metric_name="revenue", value=100, unit=unit))
    db_session.commit()
    result = AssumptionAutofillEngine.draft_assumptions(db_session, company.id)
    assert result["assumptions"]["starting_revenue"] is None
    source = result["provenance"]["starting_revenue"]
    assert source["original_value"] == 100
    assert source["requires_review"] is True
    assert source["unit_alignment_status"] == "unavailable"
    assert "starting_revenue" in result["source_metadata"]["input_readiness_summary"]["required_missing_fields"]


def test_history_growth_compares_full_currency_amounts_across_changed_reporting_scale(db_session):
    company = Company(name="Mock Data changed scale", ticker="SCALE", market="IN", currency="INR")
    db_session.add(company)
    db_session.flush()
    for year, value, unit in [(2024, 10, "INR crore"), (2025, 120, "INR million")]:
        period = FinancialStatementPeriod(company_id=company.id, year=year,
            period_type="annual", report_date=date(year, 3, 31), currency="INR")
        db_session.add(period)
        db_session.flush()
        db_session.add(FinancialMetric(period_id=period.id, metric_name="revenue", value=value, unit=unit))
    db_session.commit()
    result = AssumptionAutofillEngine.draft_assumptions(db_session, company.id)
    assert result["assumptions"]["revenue_growth_years_json"]["1"] == pytest.approx(0.2)
    source = result["provenance"]["revenue_growth_years_json"]
    assert source["history_values"] == [100_000_000, 120_000_000]
    assert source["claim_type"] == "Estimate"


def test_reporting_currency_owns_cash_flows_and_mismatched_quote_is_unavailable(db_session):
    company = Company(name="Mock Data different listing currency", ticker="FXUNIT",
        market="US", currency="USD", country="India")
    db_session.add(company)
    db_session.flush()
    period = FinancialStatementPeriod(company_id=company.id, year=date.today().year,
        period_type="annual", report_date=date.today(), currency="INR")
    db_session.add(period)
    db_session.flush()
    db_session.add(FinancialMetric(period_id=period.id, metric_name="revenue", value=100, unit="INR crore"))
    db_session.add(MarketPrice(company_id=company.id, ticker=company.ticker, price=10, currency="USD",
        as_of_date=date.today(), provider_name="test-provider", price_type="close",
        adjustment_state="unadjusted", claim_type="Fact"))
    db_session.commit()
    result = AssumptionAutofillEngine.draft_assumptions(db_session, company.id)
    assert result["assumptions"]["starting_revenue"] == 1_000_000_000
    assert result["assumptions"]["cash_flow_currency"] == "INR"
    assert result["assumptions"]["discount_rate_currency"] == "INR"
    assert result["assumptions"]["current_market_price"] is None
    assert result["provenance"]["current_market_price"]["is_placeholder"] is True
    assert any("quote currency" in warning for warning in result["warnings"])
