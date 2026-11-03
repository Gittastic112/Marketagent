import pytest
from app.models.dcf import DcfAssumptionSet
from app.services.scenario_engine import ScenarioEngine
from app.services.dcf import calculate_dcf
from test_implied_pricing_integrity import valid_inputs
from test_saved_relative_inputs import seed

@pytest.mark.parametrize("model_type", ["fcff_dcf", "distressed", "financial_services"])
def test_base_scenario_preserves_model_type(model_type):
    row = DcfAssumptionSet(id=1, valuation_model_id=1, probability_of_failure=0.4,
        distress_sale_proceeds=100, target_roe=0.15, **valid_inputs())
    expected, _, _ = calculate_dcf(row, model_type=model_type)
    results = ScenarioEngine.run_scenarios(row, model_type=model_type)
    assert len(results) == 6
    assert results[0].output.intrinsic_value_per_share == pytest.approx(expected.intrinsic_value_per_share)
    assert row.target_operating_margin == 0.22
    assert row.revenue_growth_years_json["1"] == 0.05

def test_zero_margin_and_rate_shocks_do_not_replace_zero(monkeypatch):
    from app.services import scenario_engine
    observed = []
    original = scenario_engine.calculate_dcf
    def capture(row, **kwargs):
        observed.append((row.target_operating_margin, row.wacc_start, row.wacc_terminal))
        return original(row, **kwargs)
    monkeypatch.setattr(scenario_engine, "calculate_dcf", capture)
    values = valid_inputs(); values.update(target_operating_margin=0, wacc_start=0, wacc_terminal=0)
    ScenarioEngine.run_scenarios(DcfAssumptionSet(id=1, valuation_model_id=1, **values))
    assert observed[1][0] == 0.02
    assert observed[2][0] == -0.02
    assert observed[4][1:] == (0.02, 0.02)
    assert observed[5][0] == -0.04

@pytest.mark.parametrize("invalid", ["stale", "units", "owner"])
def test_scenario_endpoint_rejects_unusable_or_unowned_inputs(client, db_session, invalid):
    _, model, row = seed(db_session)
    if invalid == "stale": row.is_stale = True
    elif invalid == "units": row.target_operating_margin = 20
    else: model.user_id = "another-owner"
    db_session.commit()
    response = client.get(f"/valuation-models/{model.id}/assumptions/{row.id}/scenarios")
    assert response.status_code == (404 if invalid == "owner" else 422)

def test_scenario_route_uses_owned_model_type(client, db_session):
    _, model, row = seed(db_session)
    for key, value in valid_inputs().items(): setattr(row, key, value)
    row.probability_of_failure = 0.4
    row.distress_sale_proceeds = 100
    model.model_type = "distressed"
    db_session.commit()
    response = client.get(f"/valuation-models/{model.id}/assumptions/{row.id}/scenarios")
    assert response.status_code == 200, response.text
    expected, _, _ = calculate_dcf(row, model_type="distressed")
    assert response.json()["data"][0]["output"]["equity_value"] == pytest.approx(expected.equity_value)
