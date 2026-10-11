import copy
import math

import pytest
from pydantic import ValidationError

from app.models.dcf import DcfAssumptionSet
from app.schemas.valuation_inputs import ReverseDcfRequest
from app.services.dcf import calculate_dcf
from app.services.reverse_dcf_engine import MarketImpliedAssumptionSolver
from test_assumption_version_integrity import saved
from test_implied_pricing_integrity import valid_inputs


@pytest.mark.parametrize("field,value", [("current_market_price", 0), ("current_market_price", -1),
    ("current_market_price", math.inf), ("diluted_shares", 0), ("diluted_shares", math.nan),
    ("target_parameter", "book_equity"), ("assumption_set_id", -1)])
def test_reverse_request_rejects_invalid_input(field, value):
    data = {"assumption_set_id": 1, "target_parameter": "target_operating_margin", "current_market_price": 100}
    data[field] = value
    with pytest.raises(ValidationError):
        ReverseDcfRequest(**data)


@pytest.mark.parametrize("invalid", ["stale", "critical", "units", "currency", "shares", "missing_core", "owner", "unsupported_model"])
def test_reverse_route_blocks_unusable_saved_basis(client, db_session, invalid):
    model, old = saved(client, db_session)
    row = db_session.get(DcfAssumptionSet, old["id"])
    if invalid == "stale": row.is_stale = True
    elif invalid == "critical": row.outputs.warnings_json = [{"severity": "critical", "module": "dcf", "message": "Review"}]
    elif invalid == "units": row.tax_rate = 25
    elif invalid == "currency": row.cash_flow_currency = None
    elif invalid == "shares": row.diluted_shares = None
    elif invalid == "missing_core": row.wacc_terminal = None
    elif invalid == "owner": model.user_id = "another-owner"
    else: model.model_type = "financial_services"
    db_session.commit()
    response = client.post("/dcf/reverse", json={"assumption_set_id": row.id,
        "target_parameter": "target_operating_margin", "current_market_price": 100})
    assert response.status_code == (404 if invalid == "owner" else 422), response.text


@pytest.mark.parametrize("model_type", ["fcff_dcf", "distressed"])
def test_solver_matches_selected_model_and_does_not_mutate_inputs(model_type):
    row = DcfAssumptionSet(id=1, valuation_model_id=1, probability_of_failure=0.4,
        distress_sale_proceeds=100, **valid_inputs())
    expected, _, _ = calculate_dcf(row, model_type=model_type)
    implied, original, warnings = MarketImpliedAssumptionSolver.solve(row, "target_operating_margin",
        expected.intrinsic_value_per_share, 10, model_type=model_type)
    assert implied == pytest.approx(0.22, abs=0.0001)
    assert original == 0.22
    assert row.target_operating_margin == 0.22
    assert row.diluted_shares == 10
    assert not any(w.severity == "blocking" for w in warnings)


def test_unreachable_target_returns_no_implied_value():
    row = DcfAssumptionSet(id=1, **valid_inputs())
    implied, _, warnings = MarketImpliedAssumptionSolver.solve(row, "target_operating_margin", 1e9, 10)
    assert implied is None
    assert any(w.severity == "blocking" for w in warnings)


def test_flat_growth_replaces_every_projection_year(monkeypatch):
    from app.services import reverse_dcf_engine
    observed = []
    calculate = reverse_dcf_engine.calculate_dcf
    def capture(row, **kwargs):
        observed.append(dict(row.revenue_growth_years_json))
        return calculate(row, **kwargs)
    monkeypatch.setattr(reverse_dcf_engine, "calculate_dcf", capture)
    values = valid_inputs(); values["revenue_growth_years_json"] = {"1": 0.05}
    MarketImpliedAssumptionSolver.solve(DcfAssumptionSet(id=1, **values), "revenue_growth", 200, 10)
    assert observed
    assert all(set(years) == {"1", "2", "3", "4", "5"} for years in observed)


def test_original_zero_is_not_replaced_with_a_default():
    values = valid_inputs(); values["terminal_growth_rate"] = 0
    _, original, _ = MarketImpliedAssumptionSolver.solve(DcfAssumptionSet(id=1, **values), "terminal_growth_rate", 200, 10)
    assert original == 0


def test_reverse_response_has_actual_residual_and_saved_basis(client, db_session):
    model, old = saved(client, db_session)
    response = client.post("/dcf/reverse", json={"assumption_set_id": old["id"],
        "target_parameter": "target_operating_margin", "current_market_price": 200, "diluted_shares": 12})
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["converged"]
    assert data["assumption_set_id"] == old["id"]
    assert data["currency"] == "USD"
    assert data["diluted_shares"] == 12
    row = copy.deepcopy(db_session.get(DcfAssumptionSet, old["id"]))
    row.target_operating_margin = data["implied_value"]
    row.diluted_shares = 12
    output, _, _ = calculate_dcf(row)
    assert data["intrinsic_value_at_implied"] == pytest.approx(output.intrinsic_value_per_share)
    assert data["price_residual"] == pytest.approx(output.intrinsic_value_per_share - 200)
    assert abs(data["price_residual"]) <= 0.01
    assert db_session.get(DcfAssumptionSet, old["id"]).target_operating_margin == old["target_operating_margin"]


def test_no_convergence_is_unavailable_in_response(client, db_session):
    _, old = saved(client, db_session)
    response = client.post("/dcf/reverse", json={"assumption_set_id": old["id"],
        "target_parameter": "target_operating_margin", "current_market_price": 1e9})
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert not data["converged"]
    assert data["implied_value"] is None
    assert data["intrinsic_value_at_implied"] is None
