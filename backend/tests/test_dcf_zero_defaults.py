"""Explicit zero is an assumption, not permission to substitute a preset."""
import math

import pytest

from app.models.dcf import DcfAssumptionSet
from app.services.dcf import (
    _calc_value_for_overrides, build_fcff_forecast, calculate_dcf,
    calculate_terminal_value, generate_sensitivity_tables,
)
from test_implied_pricing_integrity import valid_inputs
from test_saved_relative_inputs import seed


def inputs(**overrides):
    return DcfAssumptionSet(id=1, **(valid_inputs() | overrides))


def test_zero_tax_is_used_in_forecast_and_terminal_cash_flow():
    row = inputs(tax_rate=0, terminal_growth_rate=0)
    years, _, revenue, factor = build_fcff_forecast(row)
    assert all(year.tax_rate == 0 and year.nopat == year.ebit for year in years)
    tv, pv, fcff = calculate_terminal_value(row, revenue, factor)
    assert fcff == pytest.approx(revenue * .22)
    assert tv == pytest.approx(fcff / .09)
    assert pv == pytest.approx(tv / factor)


def test_zero_target_margin_fades_to_zero_instead_of_current_margin():
    row = inputs(target_operating_margin=0)
    years, _, revenue, factor = build_fcff_forecast(row)
    assert years[0].ebit_margin == pytest.approx(.16)
    assert years[-1].ebit_margin == pytest.approx(0)
    assert calculate_terminal_value(row, revenue, factor) == (0, 0, 0)


@pytest.mark.parametrize("field", ["wacc_start", "wacc_terminal"])
def test_zero_wacc_is_preserved_in_forecast(field):
    years, _, _, factor = build_fcff_forecast(inputs(**{field: 0}))
    assert (years[0] if field == "wacc_start" else years[-1]).wacc == pytest.approx(0)
    assert factor == pytest.approx(math.prod(1 + year.wacc for year in years))


def test_zero_terminal_growth_means_no_terminal_reinvestment():
    tv, _, fcff = calculate_terminal_value(inputs(terminal_growth_rate=0), 1000, 1)
    assert fcff == pytest.approx(1000 * .22 * .75)
    assert tv == pytest.approx(fcff / .09)


@pytest.mark.parametrize("field,module", [
    ("wacc_terminal", "terminal_value"),
    ("terminal_roic", "terminal_value"),
    ("sales_to_capital_ratio", "reinvestment"),
    ("diluted_shares", "equity_bridge"),
])
def test_invalid_zero_is_not_hidden_by_defaults(field, module):
    row = inputs(**{field: 0})
    output, years, _ = calculate_dcf(row)
    assert any(w["module"] == module and w["severity"] in {"critical", "blocking"}
               for w in output.warnings_json)
    if field == "wacc_terminal":
        assert output.terminal_value == 0
    elif field == "terminal_roic":
        assert any(w["module"] == "return_on_capital" for w in output.warnings_json)
    elif field == "sales_to_capital_ratio":
        assert all(year.reinvestment == 0 for year in years)
    else:
        assert output.diluted_shares == 0
        assert output.intrinsic_value_per_share == 0


@pytest.mark.parametrize("field", ["tax_rate", "target_operating_margin", "wacc_start",
    "wacc_terminal", "terminal_growth_rate", "terminal_roic", "sales_to_capital_ratio", "diluted_shares"])
def test_sensitivity_without_overrides_matches_core_with_zero(field):
    row = inputs(**{field: 0})
    output, _, _ = calculate_dcf(row)
    if field in {"wacc_terminal", "terminal_roic", "sales_to_capital_ratio", "diluted_shares"}:
        # Core historical behavior is retained; v2 grids withhold invalid cells.
        with pytest.raises(ValueError):
            _calc_value_for_overrides(row, {})
    else:
        assert _calc_value_for_overrides(row, {}) == pytest.approx(output.intrinsic_value_per_share)


@pytest.mark.parametrize("field", ["beta", "equity_risk_premium", "risk_free_rate", "pre_tax_cost_of_debt", "tax_rate"])
def test_funding_sensitivity_uses_explicit_zero_inputs(field):
    values = dict(beta=1.2, equity_risk_premium=.05, risk_free_rate=.04,
                  pre_tax_cost_of_debt=.05, debt_to_capital=.4, tax_rate=.25)
    values[field] = 0
    row = inputs(**values)
    # The unshocked funding point preserves saved WACCs and terminal ROIC, even
    # when a saved funding component is explicitly zero.
    expected, _, _ = calculate_dcf(row)
    assert _calc_value_for_overrides(row, {"debt_to_capital": .4}) == pytest.approx(expected.intrinsic_value_per_share)


@pytest.mark.parametrize("field,kind,axis", [
    ("wacc_terminal", "wacc_vs_terminal_growth", "y"),
    ("terminal_growth_rate", "wacc_vs_terminal_growth", "x"),
    ("target_operating_margin", "revenue_growth_vs_target_margin", "y"),
    ("sales_to_capital_ratio", "sales_to_capital_vs_margin", "x"),
    ("terminal_roic", "terminal_roc_vs_terminal_growth", "y"),
    ("beta", "beta_vs_equity_risk_premium", "y"),
    ("equity_risk_premium", "beta_vs_equity_risk_premium", "x"),
    ("pre_tax_cost_of_debt", "debt_ratio_vs_cost_of_debt", "x"),
])
def test_sensitivity_axis_center_retains_saved_zero(field, kind, axis):
    table = next(t for t in generate_sensitivity_tables(inputs(**{field: 0})) if t.table_type == kind)
    assert getattr(table, axis + "_axis_json")["values"][2] == 0


def test_missing_values_keep_legacy_defaults():
    missing = inputs(tax_rate=None, target_operating_margin=None, wacc_start=None,
                     wacc_terminal=None, terminal_growth_rate=None, terminal_roic=None)
    explicit = inputs(tax_rate=.21, target_operating_margin=.2, wacc_start=.1,
                      wacc_terminal=.1, terminal_growth_rate=.02, terminal_roic=.1)
    actual, _, _ = calculate_dcf(missing)
    expected, _, _ = calculate_dcf(explicit)
    assert actual.enterprise_value == pytest.approx(expected.enterprise_value)
    with pytest.raises(ValueError, match="MISSING_INPUT"):
        _calc_value_for_overrides(missing, {})
    assert _calc_value_for_overrides(explicit, {}) == pytest.approx(expected.intrinsic_value_per_share)


def test_missing_target_falls_back_to_explicit_zero_current_margin():
    row = inputs(current_operating_margin=0, target_operating_margin=None)
    output, years, tables = calculate_dcf(row)
    assert all(year.ebit_margin == 0 for year in years)
    assert output.terminal_value == 0
    table = next(t for t in tables if t.table_type == "revenue_growth_vs_target_margin")
    assert table.y_axis_json["values"][2] == 0


def test_scenario_and_reverse_consumers_keep_zero_calculation_semantics():
    from app.services.reverse_dcf_engine import MarketImpliedAssumptionSolver
    from app.services.scenario_engine import ScenarioEngine

    row = inputs(tax_rate=0, terminal_growth_rate=0, target_operating_margin=0)
    expected, _, _ = calculate_dcf(row)
    base = ScenarioEngine.run_scenarios(row)[0].output
    reverse = MarketImpliedAssumptionSolver.evaluate(row, "target_operating_margin", 0, 10, 10)
    for actual in (base, reverse):
        assert actual.terminal_value == 0
        assert actual.intrinsic_value_per_share == pytest.approx(expected.intrinsic_value_per_share)
    assert row.tax_rate == row.terminal_growth_rate == row.target_operating_margin == 0


def test_zero_horizon_is_rejected_instead_of_becoming_ten_years():
    with pytest.raises(ValueError, match="projection_years_count"):
        calculate_dcf(inputs(projection_years_count=0))
    with pytest.raises(ValueError, match="projection_years_count"):
        _calc_value_for_overrides(inputs(projection_years_count=0), {})


def test_api_zero_calculation_and_sensitivity_retain_prior_version(client, db_session):
    _, model, _ = seed(db_session)
    old = client.post(f"/valuation-models/{model.id}/assumptions", json=valid_inputs()).json()["data"]
    response = client.post(f"/valuation-models/{model.id}/assumptions", json={
        "base_assumption_set_id": old["id"], "base_assumption_set_updated_at": old["updated_at"],
        "tax_rate": 0, "terminal_growth_rate": 0, "target_operating_margin": 0,
    })
    assert response.status_code == 201, response.text
    new = response.json()["data"]
    assert new["outputs"]["terminal_value"] == 0
    years = client.get(f"/valuation-models/{model.id}/assumptions/{new['id']}/forecast").json()["data"]
    assert all(year["tax_rate"] == 0 for year in years)
    assert years[-1]["ebit_margin"] == pytest.approx(0)
    tables = client.get(f"/valuation-models/{model.id}/assumptions/{new['id']}/sensitivity").json()["data"]
    growth = next(t for t in tables if t["table_type"] == "wacc_vs_terminal_growth")
    assert growth["x_axis_json"]["values"][2] == 0
    prior = client.get(f"/valuation-models/{model.id}/assumptions/{old['id']}/results").json()["data"]
    assert prior["terminal_value"] == old["outputs"]["terminal_value"]
