"""Mock Data: independent two-year FCFF reference and saved funding shocks."""
import math

import pytest

from app.models.dcf import DcfAssumptionSet
from app.services.dcf import _calc_value_for_overrides, calculate_dcf, generate_sensitivity_tables


def assumptions(**changes):
    return DcfAssumptionSet(id=7, **(dict(projection_years_count=2, starting_revenue=1000,
        current_operating_margin=.10, target_operating_margin=.15, tax_rate=.25,
        sales_to_capital_ratio=2, starting_invested_capital=500,
        revenue_growth_years_json={"1": .10, "2": .05}, wacc_start=.12, wacc_terminal=.10,
        terminal_growth_rate=.02, terminal_roic=.18, cash=50, cross_holdings=10,
        debt=200, operating_leases=20, minority_interests=5, preferred_stock=2,
        employee_options_value=3, diluted_shares=100, current_market_price=12,
        cash_flow_currency="INR", discount_rate_currency="INR", beta=1.2,
        equity_risk_premium=.05, risk_free_rate=.04, cost_of_equity=.17,
        debt_to_capital=.4, equity_to_capital=.6, pre_tax_cost_of_debt=.05) | changes))


def reference(start=.12, terminal=.10):
    # Year FCFFs 53.125 and 102.4375; year-3 terminal FCFF 117.81.
    enterprise = 53.125 / (1 + start) + (102.4375 + 117.81 / (terminal - .02)) / ((1 + start) * (1 + terminal))
    return (enterprise - 170) / 100


def test_every_grid_center_matches_independent_saved_base():
    row = assumptions()
    original = {key: getattr(row, key) for key in ("cost_of_equity", "wacc_start", "wacc_terminal", "terminal_roic")}
    output, _, tables = calculate_dcf(row)
    assert output.intrinsic_value_per_share == pytest.approx(reference())
    for table in tables:
        x, y = table.x_axis_json["values"][2], table.y_axis_json["values"][2]
        assert table.values_json[str(round(y, 4))][str(round(x, 4))] == pytest.approx(reference())
        assert table.x_axis_json["method"]["version"] == "fcff-sensitivity-v2"
        assert table.x_axis_json["method"]["currency"] == "INR"
        assert table.x_axis_json["method"]["assumption_set_id"] == 7
    assert {key: getattr(row, key) for key in original} == original


def test_direct_rates_keep_base_and_operating_grids_without_inventing_funding_inputs():
    row = assumptions(beta=None, equity_risk_premium=None, risk_free_rate=None,
        cost_of_equity=None, debt_to_capital=None, equity_to_capital=None, pre_tax_cost_of_debt=None)
    output, _, tables = calculate_dcf(row)
    assert output.intrinsic_value_per_share == pytest.approx(reference())
    assert len(tables) == 6
    for table in tables[:4]:
        x, y = table.x_axis_json["values"][2], table.y_axis_json["values"][2]
        assert table.values_json[str(round(y, 4))][str(round(x, 4))] == pytest.approx(reference())
    for table in tables[4:]:
        assert table.x_axis_json["values"] == []
        assert table.y_axis_json["values"] == []
        assert table.values_json == {}
        assert "MISSING_FUNDING_INPUT" in table.x_axis_json["unavailable_reason"]
    with pytest.raises(ValueError, match="MISSING_FUNDING_INPUT"):
        _calc_value_for_overrides(row, {"beta": 1.2, "equity_risk_premium": .05})


@pytest.mark.parametrize("field", ["cost_of_equity", "debt_to_capital", "pre_tax_cost_of_debt", "tax_rate"])
def test_partial_funding_inputs_do_not_silently_default(field):
    changes = {field: None}
    if field == "cost_of_equity":
        changes["risk_free_rate"] = None
    with pytest.raises(ValueError, match="MISSING_FUNDING_INPUT"):
        _calc_value_for_overrides(assumptions(**changes), {"debt_to_capital": .4})


def test_explicit_capm_inputs_allow_funding_shocks_without_an_invented_equity_cost():
    row = assumptions(cost_of_equity=None)
    assert _calc_value_for_overrides(row, {"debt_to_capital": .4}) == pytest.approx(reference())
    # Explicit CAPM: .04 + 1.2 * .05 = .10. Debt shock .4 -> .5 changes
    # funding cost by .1 * (.05 * .75 - .10) = -.00625, preserving WACC fade.
    assert _calc_value_for_overrides(row, {"debt_to_capital": .5}) == pytest.approx(reference(.11375, .09375))
    assert row.cost_of_equity is None


def test_explicit_equity_cost_does_not_require_an_unused_risk_free_rate():
    row = assumptions(risk_free_rate=None)
    assert _calc_value_for_overrides(row, {"debt_to_capital": .5, "pre_tax_cost_of_debt": .06}) == pytest.approx(reference(.1105, .0905))


@pytest.mark.parametrize("overrides,delta", [
    ({"debt_to_capital": .5, "pre_tax_cost_of_debt": .06}, -.0095),
    ({"beta": 1.4, "equity_risk_premium": .06}, .0144),
])
def test_funding_changes_preserve_saved_coe_residual_wacc_fade_and_terminal_roic(overrides, delta):
    assert _calc_value_for_overrides(assumptions(), overrides) == pytest.approx(reference(.12 + delta, .10 + delta))


@pytest.mark.parametrize("changes,code", [
    ({"terminal_growth_rate": .10}, "TERMINAL_CONVERGENCE"),
    ({"terminal_growth_rate": .10 - 1e-8}, "TERMINAL_CONVERGENCE"),
    ({"sales_to_capital_ratio": 0}, "SALES_TO_CAPITAL"),
    ({"diluted_shares": 0}, "DILUTED_SHARES"),
    ({"terminal_roic": 0}, "TERMINAL_ROIC"),
    ({"wacc_terminal": None}, "MISSING_INPUT"),
    ({"diluted_shares": None}, "MISSING_INPUT"),
    ({"cash": math.inf}, "NONFINITE_INPUT"),
    ({"is_stale": True}, "STALE_INPUT"),
])
def test_unavailable_inputs_do_not_become_numeric_zero(changes, code):
    with pytest.raises(ValueError, match=code):
        _calc_value_for_overrides(assumptions(**changes), {})
    table = generate_sensitivity_tables(assumptions(**changes))[0]
    x, y = table.x_axis_json["values"][2], table.y_axis_json["values"][2]
    assert table.values_json[str(round(y, 4))][str(round(x, 4))] is None
    assert code in table.x_axis_json["cell_errors"][str(round(y, 4))][str(round(x, 4))]


def test_zero_and_negative_results_remain_numbers():
    row = assumptions(current_operating_margin=0, target_operating_margin=0,
        revenue_growth_years_json={}, cash=0, cross_holdings=0, debt=0, operating_leases=0,
        minority_interests=0, preferred_stock=0, employee_options_value=0)
    assert _calc_value_for_overrides(row, {}) == 0
    row.debt = 100
    assert _calc_value_for_overrides(row, {}) == -1


def test_nonpositive_axis_points_are_distinct_and_explicitly_unavailable():
    tables = generate_sensitivity_tables(assumptions(sales_to_capital_ratio=.25))
    table = next(item for item in tables if item.table_type == "sales_to_capital_vs_margin")
    assert len(set(table.x_axis_json["values"])) == 5
    assert table.values_json["0.15"]["0.0"] is None


def test_unsupported_distress_and_bank_do_not_receive_fcff_grids():
    assert calculate_dcf(assumptions(), model_type="distressed")[2] == []
    assert calculate_dcf(assumptions(book_value_of_equity=100, target_roe=.15), model_type="financial_services")[2] == []


def test_output_only_calculation_skips_all_grid_work(monkeypatch):
    def unexpected_grid(*args):
        raise AssertionError("Output-only callers must not calculate 150 unused grid cells")
    monkeypatch.setattr("app.services.dcf.generate_sensitivity_tables", unexpected_grid)
    output, years, tables = calculate_dcf(assumptions(), include_sensitivity=False)
    assert output.intrinsic_value_per_share == pytest.approx(reference())
    assert len(years) == 2
    assert tables == []
