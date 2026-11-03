"""Mock Data regressions for explicit specialized-model inputs and outputs."""
import math

import pytest
from pydantic import ValidationError

from app.models.dcf import DcfAssumptionSet, DcfOutput
from app.schemas.valuation_inputs import DcfAssumptionSetWrite
from app.services.dcf import calculate_dcf
from app.services.distressed_engine import DistressedCompanyEngine
from app.services.scenario_engine import ScenarioEngine
from test_implied_pricing_integrity import valid_inputs
from test_saved_relative_inputs import seed


def bank(**changes):
    data = dict(id=1, valuation_model_id=1, book_value_of_equity=100,
                net_income=10, target_roe=.1, cost_of_equity=.1,
                terminal_growth_rate=0, projection_years_count=5,
                diluted_shares=10, current_market_price=10)
    data.update(changes)
    return DcfAssumptionSet(**data)


def distress(**changes):
    data = dict(id=1, probability_of_failure=.3, distress_sale_proceeds=50,
                diluted_shares=10, current_market_price=100)
    data.update(changes)
    return DcfAssumptionSet(**data)


def base(**changes):
    data = dict(assumption_set_id=1, equity_value=1000,
                intrinsic_value_per_share=100, current_market_price=100,
                upside_downside_pct=0, diluted_shares=10)
    data.update(changes)
    return DcfOutput(**data)


@pytest.mark.parametrize("field", ["book_value_of_equity", "net_income", "target_roe",
    "cost_of_equity", "terminal_growth_rate", "diluted_shares", "projection_years_count"])
def test_bank_requires_explicit_inputs(field):
    output, projections, tables = calculate_dcf(bank(**{field: None}), "financial_services")
    assert output.intrinsic_value_per_share is None
    assert not projections and not tables
    assert any(field in w["affectedAssumptions"] and w["severity"] == "blocking"
               for w in output.warnings_json)


@pytest.mark.parametrize("field,value", [("book_value_of_equity", 0), ("book_value_of_equity", -1),
    ("diluted_shares", 0), ("diluted_shares", math.inf), ("target_roe", math.nan),
    ("cost_of_equity", math.inf), ("projection_years_count", 0), ("projection_years_count", 31),
    ("projection_years_count", 1.5), ("net_income", math.inf)])
def test_bank_invalid_inputs_fail_closed(field, value):
    output, projections, _ = calculate_dcf(bank(**{field: value}), "financial_services")
    assert output.equity_value is None and not projections
    assert output.model_quality_score == 0


def test_bank_zero_roe_income_and_growth_are_not_presets():
    output, projections, _ = calculate_dcf(bank(net_income=0, target_roe=0), "financial_services")
    assert output.equity_value == pytest.approx(0, abs=1e-10)
    assert output.upside_downside_pct == pytest.approx(-1)
    assert all(p.roic == 0 and p.revenue_growth == 0 for p in projections)
    assert output.enterprise_value is None


def test_bank_zero_equity_rate_is_valid_with_negative_growth():
    output, projections, _ = calculate_dcf(bank(cost_of_equity=0, terminal_growth_rate=-.02), "financial_services")
    assert output.equity_value > 100
    assert all(p.discount_factor == 1 for p in projections)


@pytest.mark.parametrize("growth", [.1, .2])
def test_bank_nonconvergent_terminal_is_unavailable(growth):
    output, _, _ = calculate_dcf(bank(terminal_growth_rate=growth), "financial_services")
    assert output.equity_value is None


@pytest.mark.parametrize("price", [None, 0, -1, math.inf, math.nan])
def test_bank_missing_or_invalid_price_has_no_gap(price):
    output, _, _ = calculate_dcf(bank(current_market_price=price), "financial_services")
    assert output.upside_downside_pct is None
    assert output.current_market_price is None


def test_bank_overflow_is_diagnosed_not_serialized():
    output, projections, _ = calculate_dcf(bank(book_value_of_equity=1e308,
        net_income=1e308, target_roe=1, terminal_growth_rate=.19, cost_of_equity=.2), "financial_services")
    assert output.equity_value is None and not projections


def test_distress_recalculates_price_gap_without_mutating_base():
    original = base()
    output = DistressedCompanyEngine.calculate_distressed_value(distress(), original)
    assert output.equity_value == 715
    assert output.upside_downside_pct == pytest.approx(-.285)
    assert original.equity_value == 1000 and original.upside_downside_pct == 0


@pytest.mark.parametrize("probability,expected", [(0, 1000), (1, 50)])
def test_distress_probability_endpoints(probability, expected):
    output = DistressedCompanyEngine.calculate_distressed_value(distress(probability_of_failure=probability), base())
    assert output.equity_value == expected


@pytest.mark.parametrize("field,value", [("probability_of_failure", None), ("probability_of_failure", -.1),
    ("probability_of_failure", 1.1), ("probability_of_failure", math.nan),
    ("distress_sale_proceeds", None), ("distress_sale_proceeds", -1),
    ("distress_sale_proceeds", math.inf), ("diluted_shares", None), ("diluted_shares", 0)])
def test_distress_invalid_inputs_never_fall_back(field, value):
    output = DistressedCompanyEngine.calculate_distressed_value(distress(**{field: value}), base())
    assert output.equity_value is None and output.intrinsic_value_per_share is None
    assert any(w["severity"] == "blocking" for w in output.warnings_json)


def test_distress_zero_recovery_and_complete_bridge():
    output = DistressedCompanyEngine.calculate_distressed_value(
        distress(probability_of_failure=1, distress_sale_proceeds=0),
        base(cash=10, cross_holdings=20, non_operating_assets=5, debt=40,
             operating_leases=7, minority_interests=3, preferred_stock=2, employee_options_value=1))
    assert output.intrinsic_value_per_share == 0
    assert output.upside_downside_pct == -1
    assert output.enterprise_value == 18
    assert output.terminal_value_pct_of_ev is None


@pytest.mark.parametrize("value", [None, math.nan, math.inf])
def test_distress_missing_base_is_not_zero(value):
    output = DistressedCompanyEngine.calculate_distressed_value(distress(), base(equity_value=value))
    assert output.equity_value is None


def test_distress_dispatch_retains_blocking_diagnostics():
    row = DcfAssumptionSet(id=1, **valid_inputs(), probability_of_failure=.5)
    output, _, tables = calculate_dcf(row, "distressed")
    assert output.equity_value is None and not tables
    assert any(w["module"] == "distressed_inputs" for w in output.warnings_json)
    assert output.implied_pe is None


def test_bank_scenarios_shock_equity_inputs_not_unused_fcff_fields():
    row = bank(target_roe=.15, net_income=12)
    scenarios = ScenarioEngine.run_scenarios(row, "financial_services")
    values = [s.output.equity_value for s in scenarios]
    assert len(scenarios) == 6
    assert values[1] > values[0] > values[2]
    assert values[4] < values[0]
    assert row.target_roe == .15 and row.cost_of_equity == .1


@pytest.mark.parametrize("field,value", [("probability_of_failure", -1), ("probability_of_failure", 2),
    ("distress_sale_proceeds", -1), ("distress_sale_proceeds", math.inf),
    ("target_roe", math.nan), ("book_value_of_equity", math.inf)])
def test_specialized_write_contract_rejects_invalid_values(field, value):
    with pytest.raises(ValidationError):
        DcfAssumptionSetWrite(valuation_model_id=1, **{field: value})


@pytest.mark.parametrize("price", [None, 0, -1, math.inf])
def test_distress_invalid_comparison_price_has_no_gap(price):
    output = DistressedCompanyEngine.calculate_distressed_value(distress(current_market_price=price), base())
    assert output.upside_downside_pct is None and output.current_market_price is None


def test_distress_overflow_and_invalid_bridge_are_unavailable():
    output = DistressedCompanyEngine.calculate_distressed_value(distress(diluted_shares=1e-308), base(equity_value=1e308))
    assert output.equity_value is None
    output = DistressedCompanyEngine.calculate_distressed_value(distress(), base(operating_leases=math.inf))
    assert output.equity_value is None


def test_distress_supplementary_values_do_not_masquerade_as_adjusted():
    output = DistressedCompanyEngine.calculate_distressed_value(distress(),
        base(fcfe_intrinsic_value_per_share=100, ddm_intrinsic_value_per_share=90))
    assert output.fcfe_intrinsic_value_per_share is None
    assert output.ddm_intrinsic_value_per_share is None


@pytest.mark.parametrize("model_type", ["financial_services", "distressed"])
def test_specialized_save_persists_diagnostics_and_preserves_prior_version(client, db_session, model_type):
    _, model, prior = seed(db_session)
    model.model_type = model_type
    prior_price = prior.current_market_price
    historical = DcfOutput(assumption_set_id=prior.id, equity_value=999,
        intrinsic_value_per_share=99.9, model_quality_score=88, warnings_json=[])
    db_session.add(historical)
    db_session.commit()
    inputs = valid_inputs()
    inputs.update(cost_of_equity=.1, target_roe=0, probability_of_failure=1,
                  distress_sale_proceeds=0, current_market_price=100)
    response = client.post(f"/valuation-models/{model.id}/assumptions", json=inputs)
    assert response.status_code == 201, response.text
    data = response.json()["data"]
    saved_output = data["outputs"]
    assert saved_output["warnings_json"]
    assert saved_output["model_quality_score"] is not None
    assert data["sensitivity_tables"] == []
    db_session.refresh(prior)
    assert prior.current_market_price == prior_price and prior.id != data["id"]
    old_response = client.get(f"/valuation-models/{model.id}/assumptions/{prior.id}/results")
    assert old_response.status_code == 200, old_response.text
    assert old_response.json()["data"]["equity_value"] == 999
    db_session.refresh(historical)
    assert historical.equity_value == 999 and historical.model_quality_score == 88
    if model_type == "distressed":
        assert saved_output["intrinsic_value_per_share"] == 0
        assert saved_output["upside_downside_pct"] == -1
    else:
        assert saved_output["enterprise_value"] is None


def test_missing_bank_equity_rate_is_saved_as_unavailable_not_synthetic(client, db_session):
    _, model, _ = seed(db_session)
    model.model_type = "financial_services"
    db_session.commit()
    response = client.post(f"/valuation-models/{model.id}/assumptions", json=valid_inputs())
    assert response.status_code == 201, response.text
    output = response.json()["data"]["outputs"]
    assert output["intrinsic_value_per_share"] is None
    assert output["model_quality_score"] == 0
    assert any(w["severity"] == "blocking" for w in output["warnings_json"])


def test_specialized_invalid_write_is_atomic(client, db_session):
    _, model, _ = seed(db_session)
    count = db_session.query(DcfAssumptionSet).count()
    response = client.post(f"/valuation-models/{model.id}/assumptions",
        json={**valid_inputs(), "probability_of_failure": 2})
    assert response.status_code == 422
    assert db_session.query(DcfAssumptionSet).count() == count
