"""Mock Data regression cases. No provider calls or normal database writes."""
from copy import deepcopy

import pytest
from sqlalchemy import func, select

from app.models.company import Company
from app.models.macro_sensitivity import CompanyMacroInput, CompanyMacroSensitivityResult, SectorMacroSensitivityBenchmark
from app.services.bottom_up_macro_sensitivity import BottomUpMacroSensitivityService
from app.services.macro_scenario_translation import MacroScenarioTranslationService
from app.services.top_down_macro_sensitivity import TopDownMacroSensitivityService


def periods():
    return [dict(period=str(year), operating_income=income, market_cap=value, total_debt=20,
                 change_in_long_term_bond_rate=rate, gdp_growth=0, inflation_change=0, currency_change=0)
            for year, income, value, rate in [(2021, 50, 80, 0), (2022, 49.5, 78, .01), (2023, 48.51, 74.08, .02)]]


def benchmark(db, **overrides):
    row = SectorMacroSensitivityBenchmark(source_file="Mock Data", sic_code="1234", industry_name="Fixture",
        firm_value_duration=2, firm_value_cyclicality=None, firm_value_inflation=0, firm_value_currency=.5,
        operating_income_duration=1, operating_income_cyclicality=None,
        operating_income_inflation=0, operating_income_currency=.25, **overrides)
    db.add(row)
    db.commit()
    return row


def test_constant_macro_series_is_unavailable_not_zero():
    result = TopDownMacroSensitivityService.calculate(periods(), "annual")
    assert result["firm_value"]["duration"] == pytest.approx(2)
    assert result["firm_value"]["cyclicality"] is None
    assert result["factor_diagnostics"]["gdp_growth"]["status"] == "no_variation"
    assert result["claim_type"] == "Calculation"


def test_extreme_finite_regression_inputs_fail_as_validation_not_server_error():
    inputs = periods()
    inputs[1]["gdp_growth"], inputs[2]["gdp_growth"] = 1e300, -1e300
    with pytest.raises(ValueError, match="finite range"):
        TopDownMacroSensitivityService.calculate(inputs, "annual")


def test_quarterly_selection_cannot_silently_relabel_annual_history():
    with pytest.raises(ValueError, match="frequency"):
        TopDownMacroSensitivityService.calculate(periods(), "quarterly")


def test_positive_rate_slope_is_negative_duration_not_zero():
    inputs = periods()
    inputs[1]["market_cap"], inputs[2]["market_cap"] = 82, 86.08
    result = TopDownMacroSensitivityService.calculate(inputs, "annual")
    assert result["firm_value"]["rate_slope"] == pytest.approx(2)
    assert result["firm_value"]["duration"] == pytest.approx(-2)


def test_missing_annual_period_cannot_be_compared_with_a_one_year_macro_change():
    inputs = periods()
    inputs[2]["period"] = "2024"
    with pytest.raises(ValueError, match="consecutive"):
        TopDownMacroSensitivityService.calculate(inputs, "annual")


@pytest.mark.parametrize("field", ["operating_income", "market_cap", "total_debt", "gdp_growth"])
def test_nonfinite_regression_input_rejected(field):
    inputs = periods()
    inputs[1][field] = float("inf")
    with pytest.raises(ValueError):
        TopDownMacroSensitivityService.calculate(inputs, "annual")


@pytest.mark.parametrize("labels", [["2022", "2021", "2023"], ["2021", "2021", "2023"]])
def test_regression_requires_unique_chronological_periods(labels):
    inputs = periods()
    for row, label in zip(inputs, labels):
        row["period"] = label
    with pytest.raises(ValueError):
        TopDownMacroSensitivityService.calculate(inputs, "annual")


def test_missing_active_scenario_coefficient_withholds_total(db_session):
    benchmark(db_session)
    result = MacroScenarioTranslationService.translate(db_session, sic_code="1234", rate_shock=.01,
        gdp_shock=.02, inflation_shock=0, currency_shock=0)
    assert result["estimated_value_impact_pct"] is None
    assert result["covered_value_impact_pct"] == pytest.approx(.02)
    assert result["missing_value_factors"] == ["gdp_shock"]


def test_zero_shocks_do_not_require_unused_coefficients(db_session):
    benchmark(db_session)
    result = MacroScenarioTranslationService.translate(db_session, sic_code="1234", rate_shock=0,
        gdp_shock=0, inflation_shock=.01, currency_shock=0)
    assert result["estimated_value_impact_pct"] == 0
    assert result["missing_value_factors"] == []


def test_currency_shock_requires_direction_before_estimate(db_session):
    benchmark(db_session)
    result = MacroScenarioTranslationService.translate(db_session, sic_code="1234", rate_shock=0,
        gdp_shock=0, inflation_shock=0, currency_shock=.05)
    assert result["estimated_value_impact_pct"] is None
    assert result["missing_value_factors"] == ["currency_shock"]


def test_bottom_up_separates_partial_contribution_from_whole_company(db_session):
    benchmark(db_session)
    result = BottomUpMacroSensitivityService.calculate(db_session, segments=[
        {"name": "Known", "sic_code": "1234", "value": 60},
        {"name": "Unknown", "sic_code": "9999", "value": 40}])
    assert result["duration"] is None
    assert result["firm_value"]["duration"] is None
    assert result["covered_contributions"]["duration"] == pytest.approx(1.2)
    assert result["metric_coverage"]["duration"] == pytest.approx(.6)
    assert result["metric_coverage"]["cyclicality"] == 0
    assert result["operating_income"]["duration"] is None


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf")])
def test_bottom_up_rejects_invalid_segment_value(db_session, value):
    benchmark(db_session)
    with pytest.raises(ValueError):
        BottomUpMacroSensitivityService.calculate(db_session, segments=[
            {"name": "Invalid", "sic_code": "1234", "value": value},
            {"name": "Valid", "sic_code": "1234", "value": 100}])


def test_legacy_top_down_cannot_return_fixed_coefficients_or_write(client, db_session):
    company = Company(ticker="MIMOCK", name="Mock Data company")
    db_session.add(company)
    db_session.commit()
    payload = {"company_id": company.id, "periods": [
        {"period_label": row["period"], **{key: value for key, value in row.items() if key != "period"}}
        for row in periods()]}
    response = client.post("/valuation/macro/top-down", json=payload)
    assert response.status_code == 200, response.text
    result = response.json()["data"]
    assert result["firm_value"]["duration"] == pytest.approx(2)
    assert result["firm_value"]["cyclicality"] is None
    assert db_session.scalar(select(func.count()).select_from(CompanyMacroInput)) == 0
    assert db_session.scalar(select(func.count()).select_from(CompanyMacroSensitivityResult)) == 0
    missing = deepcopy(payload)
    for row in missing["periods"]:
        row.pop("gdp_growth")
    assert client.post("/valuation/macro/top-down", json=missing).status_code == 400


def test_canonical_api_rejects_nonfinite_and_unbounded_inputs(client):
    payload = {"periods": periods()}
    payload["periods"][1]["operating_income"] = "NaN"
    assert client.post("/api/valuation/macro/top-down", json=payload).status_code == 422
    assert client.post("/api/valuation/macro/bottom-up", json={"segments": [
        {"name": "Bad", "sicCode": "1234", "value": -1}]}).status_code == 422
