"""Mock Data regression cases for saved calculation trust boundaries."""
import math
import pytest
from pydantic import ValidationError
from sqlalchemy import func, select

from app.models.dcf import DcfAssumptionSet, DcfOutput
from app.schemas.valuation_inputs import DcfAssumptionSetWrite
from test_implied_pricing_integrity import valid_inputs as base_inputs
from test_saved_relative_inputs import seed


def valid_inputs():
    return {**base_inputs(), "minority_interests": 0, "preferred_stock": 0, "employee_options_value": 0}


@pytest.mark.parametrize("growth", [{"1": True}, {"1": "0.1"}, {"1": {}}, {"1": math.nan},
    {"1": math.inf}, {"1": -1}, {"1": 6}, {"0": .1}, {"31": .1}, {"01": .1}])
def test_invalid_growth_is_rejected(growth):
    with pytest.raises(ValidationError):
        DcfAssumptionSetWrite(**{**valid_inputs(), "revenue_growth_years_json": growth})


@pytest.mark.parametrize("field", ["cash", "debt", "cross_holdings", "operating_leases", "minority_interests", "preferred_stock", "employee_options_value"])
@pytest.mark.parametrize("value", [-1, math.inf, math.nan])
def test_claims_are_nonnegative_and_finite(field, value):
    with pytest.raises(ValidationError):
        DcfAssumptionSetWrite(**{**valid_inputs(), field: value})


def test_overflow_preview_and_save_do_not_persist(client, db_session):
    _, model, _ = seed(db_session)
    inputs = {**valid_inputs(), "starting_revenue": 1e308, "revenue_growth_years_json": {"1": 5}}
    count = db_session.scalar(select(func.count()).select_from(DcfAssumptionSet))
    preview = client.post(f"/valuation-models/{model.id}/assumptions/preview", json=inputs)
    assert preview.status_code == 200, preview.text
    assert not preview.json()["data"]["ready"]
    assert preview.json()["data"]["proposed_output"] is None
    saved = client.post(f"/valuation-models/{model.id}/assumptions", json=inputs)
    assert saved.status_code == 422, saved.text
    assert db_session.scalar(select(func.count()).select_from(DcfAssumptionSet)) == count


@pytest.mark.parametrize("classification", ["sector", "industry", "damodaran_industry"])
def test_bank_context_blocks_preview_and_save_and_legacy_reads_are_nonwriting(client, db_session, classification):
    company, model, row = seed(db_session)
    setattr(company, classification, "Banks (Regional)")
    for key, value in valid_inputs().items():
        setattr(row, key, value)
    stored = DcfOutput(assumption_set_id=row.id, enterprise_value=1000, equity_value=1000,
        intrinsic_value_per_share=100, warnings_json=[])
    db_session.add(stored)
    db_session.commit()
    preview = client.post(f"/valuation-models/{model.id}/assumptions/preview", json=valid_inputs())
    assert preview.status_code == 200, preview.text
    assert not preview.json()["data"]["ready"]
    assert any(w["module"] == "model_selection" for w in preview.json()["data"]["diagnostics"])
    assert client.post(f"/valuation-models/{model.id}/assumptions", json=valid_inputs()).status_code == 422
    result = client.get(f"/valuation-models/{model.id}/assumptions/{row.id}/results").json()["data"]
    assert any(w["module"] == "model_selection" and w["severity"] == "blocking" for w in result["warnings_json"])
    summary = client.get(f"/companies/{company.id}/valuation-model-summaries").json()["data"][0]
    assert summary["readiness"] == "blocked" and summary["intrinsic_value_per_share"] is None
    scenarios = client.get(f"/valuation-models/{model.id}/assumptions/{row.id}/scenarios")
    assert scenarios.status_code == 200, scenarios.text
    assert all(any(w["module"] == "model_selection" for w in scenario["output"]["warnings_json"])
        for scenario in scenarios.json()["data"])
    db_session.refresh(stored)
    assert stored.warnings_json == [] and stored.intrinsic_value_per_share == 100


def test_legacy_invalid_claim_stays_readable_but_blocked_without_rewriting(client, db_session):
    _, model, row = seed(db_session)
    row.debt = -100
    stored = DcfOutput(assumption_set_id=row.id, enterprise_value=1000, equity_value=1100,
        intrinsic_value_per_share=110, warnings_json=[])
    db_session.add(stored); db_session.commit()
    response = client.get(f"/valuation-models/{model.id}/assumptions")
    assert response.status_code == 200, response.text
    result = response.json()["data"][0]
    assert result["debt"] == -100
    assert any(w["module"] == "input_validation" and w["severity"] == "blocking" for w in result["outputs"]["warnings_json"])
    db_session.refresh(stored); db_session.refresh(row)
    assert stored.warnings_json == [] and row.debt == -100
