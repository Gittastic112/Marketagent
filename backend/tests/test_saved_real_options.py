import math

import pytest
from sqlalchemy import func, select

from app.models.dcf import DcfAssumptionSet
from app.services.real_options_service import BlackScholesRealOptionService
from test_assumption_version_integrity import saved


def request(row, **changes):
    return dict(assumptions_updated_at=row["updated_at"], currency="USD",
        option_type="call", underlying_asset_value=100, exercise_price=100,
        option_life_years=1, risk_free_rate=.05, volatility=.2,
        dividend_yield_or_cost_of_delay=0, exclusivity_score=1,
        is_already_counted=False, confirm_incremental_equity_basis=True,
        eligibility={key: True for key in (
            "has_underlying_asset", "has_finite_life", "has_clear_exercise_price",
            "has_asymmetric_payoff", "has_exclusivity", "can_estimate_volatility",
            "can_estimate_underlying_value")}) | changes


def url(row):
    return f"/api/valuation/options/assumptions/{row['id']}/calculate"


def test_saved_option_uses_owned_total_equity_and_shares_without_writes(client, db_session):
    _, row = saved(client, db_session)
    count = db_session.scalar(select(func.count()).select_from(DcfAssumptionSet))
    response = client.post(url(row), json=request(row))
    assert response.status_code == 200, response.text
    result = response.json()["data"]
    assert result["raw_option_value"] == pytest.approx(10.450583572, abs=1e-6)
    assert result["option_value_per_share"] == pytest.approx(result["adjusted_option_value"] / 10)
    assert result["base_equity_value"] == row["outputs"]["equity_value"]
    assert result["option_adjusted_equity_value"] == pytest.approx(result["base_equity_value"] + result["adjusted_option_value"])
    assert result["option_adjusted_intrinsic_value"] == pytest.approx(result["option_adjusted_equity_value"] / 10)
    assert result["assumption_set_id"] == row["id"]
    assert result["currency"] == "USD" and len(result["input_sha256"]) == 64
    assert result["calculated_at"] and result["warnings"]
    assert any("Experimental" in note for note in result["warnings"])
    assert db_session.scalar(select(func.count()).select_from(DcfAssumptionSet)) == count


def test_fingerprint_covers_option_inputs_and_saved_output_basis(client, db_session):
    _, row = saved(client, db_session)
    first = client.post(url(row), json=request(row)).json()["data"]["input_sha256"]
    assert client.post(url(row), json=request(row)).json()["data"]["input_sha256"] == first
    assert client.post(url(row), json=request(row, exclusivity_score=0)).json()["data"]["input_sha256"] != first
    stored = db_session.get(DcfAssumptionSet, row["id"])
    stored.outputs.equity_value += 10
    stored.outputs.intrinsic_value_per_share += 1
    db_session.commit()
    assert client.post(url(row), json=request(row)).json()["data"]["input_sha256"] != first


@pytest.mark.parametrize("changes", [{"exclusivity_score": 0}, {"is_already_counted": True}])
def test_zero_exclusivity_and_double_counting_do_not_add_value(client, db_session, changes):
    _, row = saved(client, db_session)
    result = client.post(url(row), json=request(row, **changes)).json()["data"]
    assert result["option_adjusted_equity_value"] == row["outputs"]["equity_value"]


@pytest.mark.parametrize("changes", [
    {"option_type": "invalid"}, {"underlying_asset_value": 0}, {"exercise_price": -1},
    {"option_life_years": 0}, {"volatility": 0}, {"risk_free_rate": "NaN"},
    {"exclusivity_score": -1}, {"exclusivity_score": 1.1},
    {"currency": "INR"}, {"confirm_incremental_equity_basis": False},
    {"confirm_incremental_equity_basis": "true"}, {"base_dcf_value": 1e9},
    {"eligibility": {}}, {"eligibility": {"can_estimate_underlying_value": False}},
])
def test_saved_option_rejects_invalid_or_unconfirmed_input(client, db_session, changes):
    _, row = saved(client, db_session)
    assert client.post(url(row), json=request(row, **changes)).status_code == 422


@pytest.mark.parametrize("invalid", ["stale", "timestamp", "currency", "critical", "legacy_warnings",
    "shares", "output", "output_shares", "model_type", "units", "owner"])
def test_saved_option_rechecks_basis_and_ownership(client, db_session, invalid):
    model, row = saved(client, db_session)
    stored = db_session.get(DcfAssumptionSet, row["id"])
    if invalid == "stale": stored.is_stale = True
    elif invalid == "timestamp": stored.story_text = "changed"
    elif invalid == "currency": stored.cash_flow_currency = None
    elif invalid == "critical": stored.outputs.warnings_json = [{"severity": "critical", "module": "test", "message": "blocked"}]
    elif invalid == "legacy_warnings": stored.outputs.warnings_json = ["unknown"]
    elif invalid == "shares": stored.diluted_shares = None
    elif invalid == "output": stored.outputs.equity_value = None
    elif invalid == "output_shares": stored.outputs.diluted_shares = 999
    elif invalid == "model_type": model.model_type = "distressed"
    elif invalid == "units": stored.tax_rate = 25
    else: model.user_id = "other-owner"
    db_session.commit()
    assert client.post(url(row), json=request(row)).status_code == (404 if invalid == "owner" else 422)


@pytest.mark.parametrize("changes", [{"S": math.inf}, {"r": math.nan}, {"exclusivity_score": -1}, {"option_type": "typo"}])
def test_pure_engine_rejects_nonfinite_or_invalid_inputs(changes):
    with pytest.raises(ValueError):
        BlackScholesRealOptionService.calculate(**(dict(S=100, K=100, t=1, r=.05, sigma=.2, y=0) | changes))
