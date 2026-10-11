from datetime import datetime, UTC
import math

import pytest

from app.api.schemas import DcfOutputCreate, DcfOutputRead
from app.models.dcf import DcfAssumptionSet, DcfOutput
from app.services.relative_valuation_service import RelativeValuationService, implied_pricing, RATIO_FIELDS
from test_saved_relative_inputs import seed


def output(**overrides):
    return DcfOutputCreate(assumption_set_id=1, enterprise_value=1000, equity_value=800, **overrides)


def test_ratios_use_explicit_saved_denominators():
    result = output()
    row = DcfAssumptionSet(starting_revenue=100, current_operating_margin=0.2,
        net_income=10, book_value_of_equity=200, debt=1000, wacc_start=0.9, tax_rate=0)
    RelativeValuationService.calculate_implied_multiples(result, row)
    assert (result.implied_pe, result.implied_pbv, result.implied_ev_sales, result.implied_ev_ebit) == (80, 4, 10, 50)
    assert result.implied_ev_ebitda is None


@pytest.mark.parametrize("income", [None, 0, -10, math.inf, math.nan, True])
def test_missing_loss_and_invalid_income_never_get_proxy_pe(income):
    result = output(implied_pe=999)
    row = DcfAssumptionSet(starting_revenue=100, current_operating_margin=0.2, net_income=income)
    RelativeValuationService.calculate_implied_multiples(result, row)
    assert result.implied_pe is None
    assert result.implied_ev_sales == 10


@pytest.mark.parametrize("depreciation", [None, 0, 40])
def test_ebitda_proxy_is_cleared_even_when_depreciation_exists(depreciation):
    result = output(implied_ev_ebitda=999)
    RelativeValuationService.calculate_implied_multiples(result,
        DcfAssumptionSet(starting_revenue=100, current_operating_margin=0.2, depreciation=depreciation))
    assert result.implied_ev_ebitda is None


@pytest.mark.parametrize("value", [None, math.inf, math.nan])
def test_missing_or_nonfinite_dcf_values_do_not_become_zero(value):
    result = output()
    result.equity_value = value
    RelativeValuationService.calculate_implied_multiples(result, DcfAssumptionSet(net_income=10))
    assert result.implied_pe is None


def test_zero_dcf_value_remains_zero_and_overflow_is_unavailable():
    result = output()
    result.equity_value = 0
    RelativeValuationService.calculate_implied_multiples(result, DcfAssumptionSet(net_income=10))
    assert result.implied_pe == 0
    result.equity_value = 1e308
    RelativeValuationService.calculate_implied_multiples(result, DcfAssumptionSet(net_income=1e-308))
    assert result.implied_pe is None


@pytest.mark.parametrize("row", [DcfAssumptionSet(starting_revenue=100),
    DcfAssumptionSet(current_operating_margin=0.2),
    DcfAssumptionSet(starting_revenue=100, current_operating_margin=20)])
def test_ebit_requires_valid_operands(row):
    result = output(implied_ev_ebit=999)
    RelativeValuationService.calculate_implied_multiples(result, row)
    assert result.implied_ev_ebit is None


@pytest.mark.parametrize("blocked", ["stale", "critical", "blocking"])
def test_trust_blockers_suppress_all_pricing_ratios(blocked):
    row = DcfAssumptionSet(starting_revenue=100, net_income=10, is_stale=blocked == "stale")
    result = output(warnings_json=[] if blocked == "stale" else [{"module": "dcf", "severity": blocked}])
    RelativeValuationService.calculate_implied_multiples(result, row)
    assert all(getattr(result, field) is None for field in RATIO_FIELDS)


def test_contextless_output_read_hides_legacy_ratios_and_pricing_warnings():
    result = DcfOutputRead.model_validate({"id": 1, "assumption_set_id": 1,
        "created_at": datetime.now(UTC), "implied_pe": 999, "implied_ev_ebitda": 999,
        "warnings_json": [{"module": "relative_pricing", "message": "Old proxy advice"}]})
    assert result.implied_pe is None
    assert result.implied_ev_ebitda is None
    assert result.warnings_json == []
    assert "context" in result.implied_pricing_basis["methods"][0]["reason"]


def test_historical_list_and_result_reads_reconcile_without_writing(client, db_session):
    _, model, row = seed(db_session)
    stored = DcfOutput(assumption_set_id=row.id, enterprise_value=1000, equity_value=800,
        implied_pe=999, implied_ev_ebitda=888, warnings_json=[
            {"module": "relative_pricing", "message": "Old proxy advice"},
            {"module": "cash", "severity": "watch", "message": "Keep unrelated warning"}])
    db_session.add(stored)
    db_session.commit()
    listed = client.get(f"/valuation-models/{model.id}/assumptions").json()["data"][0]["outputs"]
    direct = client.get(f"/valuation-models/{model.id}/assumptions/{row.id}/results").json()["data"]
    detail = client.get(f"/valuation-models/{model.id}").json()["data"]["assumption_sets"][0]["outputs"]
    for result in (listed, direct, detail):
        assert result["implied_pe"] == 8
        assert result["implied_ev_ebitda"] is None
        assert result["implied_pbv"] == 1.6
        assert result["warnings_json"] == [{"module": "cash", "severity": "watch", "message": "Keep unrelated warning"}]
        assert result["implied_pricing_basis"]["assumptionSetId"] == row.id
        assert result["implied_pricing_basis"]["outputCreatedAt"]
        assert result["implied_pricing_basis"]["assumptionsUpdatedAt"]
    db_session.refresh(stored)
    assert stored.implied_pe == 999
    assert stored.implied_ev_ebitda == 888
    assert stored.warnings_json[0]["message"] == "Old proxy advice"


def test_diagnostics_disclose_heuristics_without_proxy_adjustment_advice():
    result = output(implied_pe=80, implied_ev_sales=20, implied_ev_ebitda=1)
    warnings = RelativeValuationService.generate_relative_pricing_diagnostics(result)
    assert len(warnings) == 2
    assert all("heuristic" in warning.message for warning in warnings)
    assert all("Proxy" not in (warning.formula or "") for warning in warnings)


def test_pricing_reads_preserve_owned_resource_boundary(client, db_session):
    _, model, row = seed(db_session)
    model.user_id = "another-owner"
    db_session.commit()
    for path in (f"/valuation-models/{model.id}",
        f"/valuation-models/{model.id}/assumptions",
        f"/valuation-models/{model.id}/assumptions/{row.id}/results"):
        assert client.get(path).status_code == 404


def valid_inputs():
    return dict(projection_years_count=5, starting_revenue=1000,
        current_operating_margin=0.2, target_operating_margin=0.22, tax_rate=0.25,
        revenue_growth_years_json={str(i): 0.05 for i in range(1, 6)},
        sales_to_capital_ratio=2.5, starting_invested_capital=600,
        wacc_start=0.10, wacc_terminal=0.09, terminal_growth_rate=0.02,
        terminal_roic=0.12, cash=0, debt=0, diluted_shares=10,
        net_income=100, book_value_of_equity=500,
        cash_flow_currency="USD", discount_rate_currency="USD")


def test_new_save_persists_explicit_ratios_and_returns_basis(client, db_session):
    _, model, _ = seed(db_session)
    response = client.post(f"/valuation-models/{model.id}/assumptions", json=valid_inputs())
    assert response.status_code == 201, response.text
    result = response.json()["data"]["outputs"]
    assert result["implied_pe"] == pytest.approx(result["equity_value"] / 100)
    assert result["implied_pbv"] == pytest.approx(result["equity_value"] / 500)
    assert result["implied_ev_ebitda"] is None
    stored = db_session.get(DcfOutput, result["id"])
    assert stored.implied_pe == result["implied_pe"]
    assert stored.implied_ev_ebitda is None


def test_scenario_reads_keep_their_own_calculated_numerators():
    from app.services.scenario_engine import ScenarioEngine
    row = DcfAssumptionSet(id=1, valuation_model_id=1, **valid_inputs())
    scenarios = ScenarioEngine.run_scenarios(row)
    assert len(scenarios) == 6
    for scenario in scenarios:
        result = scenario.output
        assert result.implied_pe == pytest.approx(result.equity_value / 100)
        assert result.implied_ev_ebitda is None
        assert result.implied_pricing_basis["assumptionSetId"] == 1
    assert scenarios[0].output.implied_pe != scenarios[1].output.implied_pe


def test_distressed_ratios_use_final_adjusted_values():
    from app.services.dcf import calculate_dcf
    row = DcfAssumptionSet(id=1, valuation_model_id=1, probability_of_failure=0.4,
        distress_sale_proceeds=100, **valid_inputs())
    result, _, _ = calculate_dcf(row, model_type="distressed")
    assert result.equity_value != result.base_dcf_value
    assert result.implied_pe == pytest.approx(result.equity_value / 100)
    assert result.implied_ev_sales == pytest.approx(result.enterprise_value / 1000)
