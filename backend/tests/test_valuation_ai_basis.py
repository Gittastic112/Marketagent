"""AI explanation must retain the exact saved calculation and review boundary."""
import pytest
from sqlalchemy import func, select

from app.models.ai import AiOutput
from app.models.dcf import DcfAssumptionSet
from test_assumption_version_integrity import saved, basis


def memo_path(model):
    return f"/valuation/{model.id}/scenarios/Base/ai/memo"


def request_basis(row):
    return {"assumption_set_id": row["id"], "assumptions_updated_at": row["updated_at"],
            "privacy_disclosure_version": "v1"}


def test_memo_default_selects_newest_saved_version_and_exposes_evidence(client, db_session):
    model, old = saved(client, db_session)
    latest = client.post(f"/valuation-models/{model.id}/assumptions", json={
        **basis(old), "story_text": "Mock Data current saved story"}).json()["data"]
    response = client.post(memo_path(model), json={"privacy_disclosure_version": "v1"})
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    evidence = data["evidence"]
    assert evidence["assumption_set_id"] == latest["id"]
    assert evidence["output_id"] == latest["outputs"]["id"]
    assert evidence["currency"] == "USD"
    assert evidence["review_status"] == "pending"
    assert evidence["claim_type"] == "AI Interpretation"
    assert evidence["source_ids"] == [f"company:{model.company_id}", f"valuation:{model.id}",
                                      f"dcf_assumption_set:{latest['id']}"]
    assert len(evidence["input_hash"]) == 64
    assert evidence["prompt_version"] and evidence["model_name"] and evidence["generated_at"]
    assert evidence["is_mock"] is True
    assert db_session.get(AiOutput, evidence["ai_output_id"]).reference_id == latest["id"]
    assert client.get(memo_path(model)).json()["data"]["evidence"] == evidence


@pytest.mark.parametrize("operation", ["memo", "narrative-to-numbers"])
@pytest.mark.parametrize("conflict", ["new_version", "changed_timestamp", "foreign_id"])
def test_outdated_basis_is_rejected_before_provider_call(client, db_session, operation, conflict):
    model, old = saved(client, db_session)
    payload = {**request_basis(old), "narrative_text": "Mock Data review this story"}
    if conflict == "new_version":
        client.post(f"/valuation-models/{model.id}/assumptions", json={**basis(old), "cash": 123})
    elif conflict == "changed_timestamp":
        row = db_session.get(DcfAssumptionSet, old["id"])
        row.story_text = "Changed by another request"
        db_session.commit()
    else:
        payload["assumption_set_id"] += 1000000
    before = db_session.scalar(select(func.count()).select_from(AiOutput))
    response = client.post(f"/valuation/{model.id}/scenarios/Base/ai/{operation}", json=payload)
    assert response.status_code == 409, response.text
    assert db_session.scalar(select(func.count()).select_from(AiOutput)) == before


@pytest.mark.parametrize("blocked", ["stale", "invalid_units", "critical", "missing_output"])
def test_memo_cannot_explain_unusable_output_as_current(client, db_session, blocked):
    model, row = saved(client, db_session)
    stored = db_session.get(DcfAssumptionSet, row["id"])
    if blocked == "stale":
        stored.is_stale = True
    elif blocked == "invalid_units":
        stored.wacc_start = 9
    elif blocked == "critical":
        stored.outputs.warnings_json = [{"module": "dcf", "severity": "critical", "message": "Review units"}]
    else:
        db_session.delete(stored.outputs)
    db_session.commit()
    before = db_session.scalar(select(func.count()).select_from(AiOutput))
    response = client.post(memo_path(model), json={"privacy_disclosure_version": "v1"})
    assert response.status_code == 409, response.text
    assert db_session.scalar(select(func.count()).select_from(AiOutput)) == before


def test_historical_memo_is_read_only_and_never_substituted_for_new_version(client, db_session):
    model, old = saved(client, db_session)
    generated = client.post(memo_path(model), json=request_basis(old)).json()["data"]
    assert generated.get("memo_markdown")
    latest = client.post(f"/valuation-models/{model.id}/assumptions", json={
        **basis(old), "cash": 123}).json()["data"]
    count = db_session.scalar(select(func.count()).select_from(AiOutput))
    assert client.get(memo_path(model)).json()["data"]["memo_markdown"] is None
    history = client.get(memo_path(model), params={"assumption_set_id": old["id"]}).json()["data"]
    assert history["evidence"]["assumption_set_id"] == old["id"]
    assert history["evidence"]["is_current"] is False
    assert client.get(memo_path(model), params={"assumption_set_id": latest["id"]}).json()["data"]["memo_markdown"] is None
    assert client.get(memo_path(model), params={"assumption_set_id": 999999}).status_code == 404
    assert db_session.scalar(select(func.count()).select_from(AiOutput)) == count


def test_narrative_retains_exact_basis_and_ai_provenance(client, db_session):
    model, row = saved(client, db_session)
    response = client.post(f"/valuation/{model.id}/scenarios/Base/ai/narrative-to-numbers", json={
        **request_basis(row), "narrative_text": "Mock Data: growth with uncertain margins"})
    assert response.status_code == 200, response.text
    evidence = response.json()["data"]["evidence"]
    assert evidence["assumption_set_id"] == row["id"]
    assert evidence["review_status"] == "pending"
    assert db_session.get(AiOutput, evidence["ai_output_id"]).reference_id == row["id"]
    assert db_session.get(DcfAssumptionSet, row["id"]).story_text is None


def test_changed_calculation_cannot_keep_an_earlier_memo_current(client, db_session):
    model, row = saved(client, db_session)
    generated = client.post(memo_path(model), json=request_basis(row)).json()["data"]
    assert len(generated["evidence"]["output_hash"]) == 64
    stored = db_session.get(DcfAssumptionSet, row["id"])
    stored.outputs.equity_value += 1
    db_session.commit()
    response = client.get(memo_path(model)).json()["data"]
    assert response["evidence"]["output_hash"] == generated["evidence"]["output_hash"]
    assert response["evidence"]["is_current"] is False


def test_malformed_legacy_calculation_preserves_memo_history_without_verifying_it(client, db_session):
    model, row = saved(client, db_session)
    assert client.post(memo_path(model), json=request_basis(row)).status_code == 200
    db_session.get(DcfAssumptionSet, row["id"]).outputs.equity_value = float("inf")
    db_session.commit()
    response = client.get(memo_path(model))
    assert response.status_code == 200
    assert response.json()["data"]["evidence"]["is_current"] is False
    assert client.post(memo_path(model), json=request_basis(row)).status_code == 409


@pytest.mark.parametrize("action", ["evaluate", "review", "citations"])
def test_evaluation_and_review_preserve_the_original_saved_valuation_basis(client, db_session, action):
    model, row = saved(client, db_session)
    generated = client.post(memo_path(model), json=request_basis(row)).json()["data"]["evidence"]
    output_id = generated["ai_output_id"]
    original = dict(db_session.get(AiOutput, output_id).evaluation_json["valuation_basis"])
    if action == "review":
        response = client.patch(f"/ai-outputs/{output_id}/review", json={"status": "needs_revision", "notes": "Mock Data human review"})
    elif action == "citations":
        response = client.post(f"/ai-outputs/{output_id}/citations/validate", json={"citations": [
            {"source_id": f"company:{model.company_id}", "quote": "Mock Data unverified citation"}]})
    else:
        response = client.post(f"/ai-outputs/{output_id}/evaluate")
    assert response.status_code == 200, response.text
    assert db_session.get(AiOutput, output_id).evaluation_json["valuation_basis"] == original
    current = client.get(memo_path(model)).json()["data"]["evidence"]
    assert current["basis_verified"] and current["is_current"]
    for key in ("assumption_set_id", "output_id", "output_hash", "assumptions_updated_at", "output_calculated_at", "currency"):
        assert current[key] == generated[key]
    assert current["review_status"] == ("needs_revision" if action == "review" else "pending")
