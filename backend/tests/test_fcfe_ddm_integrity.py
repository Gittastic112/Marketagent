"""Supplementary equity models use explicit inputs, never WACC or one-share presets."""
import math

import pytest

from app.models.dcf import DcfAssumptionSet
from app.services.dcf import calculate_dcf
from app.services.fcfe_ddm_engine import FCFEEngine, DividendDiscountEngine, CompanyCashReturnService
from test_implied_pricing_integrity import valid_inputs
from test_saved_relative_inputs import seed


def inputs(**changes):
    return DcfAssumptionSet(id=1, **(valid_inputs() | dict(
        cost_of_equity=.12, terminal_growth_rate=0, net_income=100,
        capex=30, depreciation=10, change_in_nwc=5, new_debt_issued=10,
        debt_repaid=5, dividends=40, buybacks=0, stock_issuances=0,
    ) | changes))


def values(row):
    fcfe = FCFEEngine.calculate_fcfe(row)
    return (FCFEEngine.calculate_fcfe_intrinsic_value(row, fcfe) if fcfe is not None else None,
            DividendDiscountEngine.calculate_ddm_intrinsic_value(row))


def test_zero_growth_uses_explicit_equity_rate_not_wacc():
    row = inputs()
    assert FCFEEngine.calculate_fcfe(row) == 80
    assert values(row) == pytest.approx((80 / .12 / 10, 40 / .12 / 10))
    assert values(inputs(wacc_terminal=.3)) == values(row)


def test_nonzero_growth_applies_to_next_year_cash_flow():
    assert values(inputs(terminal_growth_rate=.02)) == pytest.approx((81.6 / .10 / 10, 40.8 / .10 / 10))


def test_zero_cash_flow_and_dividends_remain_zero_estimates():
    assert values(inputs(net_income=20, dividends=0)) == (0, 0)


def test_zero_equity_rate_is_not_replaced_and_negative_growth_can_converge():
    assert values(inputs(cost_of_equity=0, terminal_growth_rate=0)) == (None, None)
    assert values(inputs(cost_of_equity=0, terminal_growth_rate=-.02)) == pytest.approx((78.4 / .02 / 10, 39.2 / .02 / 10))


@pytest.mark.parametrize("field,value", [
    ("cost_of_equity", None), ("terminal_growth_rate", None), ("diluted_shares", None),
    ("diluted_shares", 0), ("diluted_shares", -1), ("cost_of_equity", math.nan),
    ("cost_of_equity", math.inf), ("cost_of_equity", -.01), ("cost_of_equity", 12),
    ("terminal_growth_rate", .12), ("terminal_growth_rate", math.nan),
    ("terminal_growth_rate", -1), ("diluted_shares", math.inf),
    ("diluted_shares", 1e-320), ("cost_of_equity", True),
])
def test_missing_invalid_or_nonfinite_basis_is_unavailable(field, value):
    assert values(inputs(**{field: value})) == (None, None)


@pytest.mark.parametrize("field", ["net_income", "capex", "depreciation", "change_in_nwc", "new_debt_issued", "debt_repaid"])
@pytest.mark.parametrize("value", [None, math.nan, math.inf])
def test_fcfe_requires_complete_finite_cash_flow_components(field, value):
    assert FCFEEngine.calculate_fcfe(inputs(**{field: value})) is None


def test_explicit_zero_components_are_complete_and_overflow_is_unavailable():
    row = inputs(net_income=0, capex=0, depreciation=0, change_in_nwc=0, new_debt_issued=0, debt_repaid=0)
    assert FCFEEngine.calculate_fcfe(row) == 0
    assert FCFEEngine.calculate_fcfe(inputs(net_income=1e308, depreciation=1e308)) is None
    assert values(inputs(net_income=-100, dividends=-1)) == (None, None)


def test_cash_return_requires_complete_finite_inputs_and_keeps_zero():
    assert CompanyCashReturnService.calculate_net_cash_returned(inputs(dividends=0)) == 0
    for value in (None, math.nan, math.inf):
        assert CompanyCashReturnService.calculate_net_cash_returned(inputs(buybacks=value)) is None


def test_missing_supplementary_basis_warns_without_changing_core_dcf():
    complete, _, _ = calculate_dcf(inputs())
    incomplete, _, _ = calculate_dcf(inputs(cost_of_equity=None, capex=None))
    assert complete.intrinsic_value_per_share == incomplete.intrinsic_value_per_share
    assert incomplete.fcfe_intrinsic_value_per_share is None
    assert incomplete.ddm_intrinsic_value_per_share is None
    notices = [w for w in incomplete.warnings_json if w["module"] == "supplementary_equity"]
    assert len(notices) == 2 and all(w["severity"] == "watch" for w in notices)
    assert any("capex" in w["affectedAssumptions"] for w in notices)


def test_payout_diagnostics_use_saved_currency_and_do_not_assert_causation():
    output, _, _ = calculate_dcf(inputs(dividends=90, buybacks=30, stock_issuances=20,
        current_market_price=1000, cash_flow_currency="INR", discount_rate_currency="INR"))
    notices = [w["message"] for w in output.warnings_json if w["module"] == "payout_policy"]
    assert notices and all("$" not in w for w in notices)
    assert any("INR" in w for w in notices)
    assert not any("destroys shareholder value" in w or "The company is borrowing" in w for w in notices)


def test_scenario_consumers_preserve_explicit_equity_basis():
    from app.services.scenario_engine import ScenarioEngine
    row = inputs()
    for scenario in ScenarioEngine.run_scenarios(row):
        assert scenario.output.fcfe_intrinsic_value_per_share == pytest.approx(80 / .12 / 10)
        assert scenario.output.ddm_intrinsic_value_per_share == pytest.approx(40 / .12 / 10)
    assert row.terminal_growth_rate == 0


def test_new_version_persists_equity_math_without_rewriting_history(client, db_session):
    _, model, _ = seed(db_session)
    payload = {column.name: getattr(inputs(), column.name) for column in DcfAssumptionSet.__table__.columns
               if column.name not in {"id", "valuation_model_id", "created_at", "updated_at"}}
    # The API creates omitted defaults itself, not this transient ORM fixture.
    payload = {key: value for key, value in payload.items() if value is not None}
    first = client.post(f"/valuation-models/{model.id}/assumptions", json=payload)
    assert first.status_code == 201, first.text
    old = first.json()["data"]
    stored = db_session.get(DcfAssumptionSet, old["id"])
    stored.outputs.fcfe_intrinsic_value_per_share = 999  # A labeled historical legacy result.
    db_session.commit()
    response = client.post(f"/valuation-models/{model.id}/assumptions", json={
        "base_assumption_set_id": old["id"], "base_assumption_set_updated_at": old["updated_at"],
        "dividends": 0, "cost_of_equity": .1,
    })
    assert response.status_code == 201, response.text
    new = response.json()["data"]
    assert new["outputs"]["fcfe_intrinsic_value_per_share"] == pytest.approx(80)
    assert new["outputs"]["ddm_intrinsic_value_per_share"] == 0
    detail = client.get(f"/valuation-models/{model.id}").json()["data"]
    historical = next(row for row in detail["assumption_sets"] if row["id"] == old["id"])
    assert historical["outputs"]["fcfe_intrinsic_value_per_share"] == 999
    db_session.expire_all()
    assert db_session.get(DcfAssumptionSet, old["id"]).outputs.fcfe_intrinsic_value_per_share == 999
