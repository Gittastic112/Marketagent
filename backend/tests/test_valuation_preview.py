from uuid import uuid4

from sqlalchemy import func, select

from app.models.dcf import DcfAssumptionSet, DcfDecisionLog
from test_assumption_version_integrity import saved, basis


def proposal(client, db):
    model, old = saved(client, db)
    request = {**basis(old), "cash": 5, "minority_interests": 0, "preferred_stock": 0,
        "employee_options_value": 0, "valuation_date": "2026-11-12"}
    return model, old, request


def test_preview_is_deterministic_read_only_and_saves_exactly_once(client, db_session):
    model, old, request = proposal(client, db_session)
    url = f"/valuation-models/{model.id}/assumptions"
    before = db_session.scalar(select(func.count()).select_from(DcfAssumptionSet))
    response = client.post(url + "/preview", json=request)
    assert response.status_code == 200, response.text
    preview = response.json()["data"]
    assert preview["ready"] and preview["proposed_output"]
    assert preview["preview_hash"] == client.post(url + "/preview", json=request).json()["data"]["preview_hash"]
    assert {r["field"] for r in preview["changes"]} >= {"cash"}
    assert db_session.scalar(select(func.count()).select_from(DcfAssumptionSet)) == before
    command = {**request, "preview_hash": preview["preview_hash"], "submission_id": str(uuid4()),
        "change_reason": "Mock Data reviewed source change"}
    first = client.post(url, json=command)
    assert first.status_code == 201, first.text
    second = client.post(url, json=command)
    assert second.status_code == 201 and second.json()["data"]["id"] == first.json()["data"]["id"]
    assert db_session.scalar(select(func.count()).select_from(DcfAssumptionSet)) == before + 1
    assert db_session.get(DcfAssumptionSet, old["id"]).cash == 0
    assert first.json()["data"]["outputs"]["equity_value"] == preview["proposed_output"]["equity_value"]
    receipt = client.get(f"/valuation-models/{model.id}/version-receipts").json()["data"][0]
    assert receipt["valuation_date"] == "2026-11-12" and receipt["previous_assumption_set_id"] == old["id"]
    assert client.post(url, json={**command, "cash": 6}).status_code == 409


def test_preview_change_and_missing_shares_fail_without_writes(client, db_session):
    model, _, request = proposal(client, db_session)
    url = f"/valuation-models/{model.id}/assumptions"
    preview = client.post(url + "/preview", json=request).json()["data"]
    command = {**request, "cash": 7, "preview_hash": preview["preview_hash"],
        "submission_id": str(uuid4()), "change_reason": "Mock Data reason"}
    assert client.post(url, json=command).status_code == 409
    missing = client.post(url + "/preview", json={**request, "diluted_shares": None}).json()["data"]
    assert not missing["ready"] and "diluted_shares" in missing["missing_fields"]
    assert missing["proposed_output"] is None
    assert client.post(url, json={**request, "diluted_shares": None}).status_code == 422
    assert db_session.scalar(select(func.count()).select_from(DcfDecisionLog)) == 0


def test_preview_rejects_other_owner_and_stale_basis(client, db_session):
    model, old, request = proposal(client, db_session)
    url = f"/valuation-models/{model.id}/assumptions/preview"
    assert client.post(f"/valuation-models/999999/assumptions/preview", json=request).status_code == 404
    row = db_session.get(DcfAssumptionSet, old["id"]); row.is_stale = True; db_session.commit()
    assert client.post(url, json=request).status_code == 409
