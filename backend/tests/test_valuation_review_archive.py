"""Mock Data review receipts bind the observed state; archives preserve raw evidence."""
import json
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.models.dcf import DcfAssumptionSet, DcfDecisionLog, DcfOutput, ValuationAssumptionChangeLog
from test_assumption_version_integrity import saved
from test_saved_relative_inputs import seed


def stale(db, client):
    model, prior = saved(client, db)
    row = db.get(DcfAssumptionSet, prior["id"])
    row.is_stale = True; row.stale_reason = "Mock Data source change"
    db.commit()
    viewed = client.get(f"/valuation-models/{model.id}/assumptions").json()["data"][0]
    return model, row, {"expected_updated_at": viewed["updated_at"], "review_token": viewed["stale_review_token"],
        "reason": "Reviewed the Mock Data source; keep these assumptions."}


@pytest.mark.parametrize("change", ["timestamp", "reason", "new_log"])
def test_outdated_acknowledgement_never_clears_new_review_state(db, client, change):
    model, row, request = stale(db, client)
    if change == "timestamp": row.updated_at += timedelta(seconds=1)
    elif change == "reason": row.stale_reason = "Mock Data newer trigger"
    else:
        db.add(ValuationAssumptionChangeLog(valuation_model_id=model.id, assumption_set_id=row.id,
            parameter_name="cash", old_value="1", new_value="2", rationale="Mock Data another review"))
    db.commit()
    response = client.post(f"/valuation-models/{model.id}/assumptions/{row.id}/resolve-stale", json=request)
    assert response.status_code == 409, response.text
    db.refresh(row)
    assert row.is_stale and not list(db.scalars(select(DcfDecisionLog).where(DcfDecisionLog.decision_type == "stale_review")))


def test_explicit_unchanged_review_records_receipt_and_rejects_replay_or_missing_basis(db, client):
    model, row, request = stale(db, client)
    url = f"/valuation-models/{model.id}/assumptions/{row.id}/resolve-stale"
    assert client.post(url, json={}).status_code == 422
    assert client.post(url, json={**request, "reason": " " * 12}).status_code == 422
    before = row.cash
    response = client.post(url, json=request)
    assert response.status_code == 200, response.text
    db.refresh(row)
    assert row.is_stale is False and row.cash == before
    receipt = db.scalar(select(DcfDecisionLog).where(DcfDecisionLog.decision_type == "stale_review"))
    assert json.loads(receipt.user_note)["review_token"] == request["review_token"]
    assert json.loads(receipt.user_note)["reason"] == request["reason"]
    assert client.post(url, json=request).status_code == 409
    model.user_id = "another-owner"; db.commit()
    assert client.post(url, json=request).status_code == 404


def test_exact_archive_preserves_legacy_output_warnings_and_zeroes_without_writing(db, client):
    _, model, row = seed(db)
    original_warnings = [{"module": "relative_pricing", "message": "Mock Data historical proxy warning"},
        {"module": "cash", "severity": "watch", "message": "Mock Data original diagnostic"}]
    output = DcfOutput(assumption_set_id=row.id, enterprise_value=1000, equity_value=800,
        implied_pe=999, implied_ev_ebitda=888, warnings_json=original_warnings)
    row.cash = 0
    db.add(output); db.commit()
    interpreted = client.get(f"/valuation-models/{model.id}/assumptions").json()["data"][0]
    assert interpreted["outputs"]["implied_pe"] != 999
    response = client.get(f"/valuation-models/{model.id}/assumptions/{row.id}/export")
    assert response.status_code == 200, response.text
    archive = response.json()["data"]
    assert archive["export_kind"] == "raw_saved_valuation_v1"
    raw = archive["saved_version"]
    assert raw["outputs"]["implied_pe"] == 999 and raw["outputs"]["implied_ev_ebitda"] == 888
    assert raw["outputs"]["warnings_json"] == original_warnings and raw["cash"] == 0
    db.refresh(output)
    assert output.warnings_json == original_warnings and output.implied_pe == 999
    assert not db.dirty
    model.user_id = "another-owner"; db.commit()
    assert client.get(f"/valuation-models/{model.id}/assumptions/{row.id}/export").status_code == 404
