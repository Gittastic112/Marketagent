"""Versioned form saves must preserve omitted inputs, never overwrite a newer basis."""
import pytest
from sqlalchemy import select, func

from app.models.dcf import DcfAssumptionSet, ValuationAssumptionChangeLog
from test_saved_relative_inputs import seed
from test_implied_pricing_integrity import valid_inputs


def saved(client, db_session):
    _, model, _ = seed(db_session)
    response = client.post(f"/valuation-models/{model.id}/assumptions", json={
        **valid_inputs(), "target_roe": 0, "probability_of_failure": 0,
        "distress_sale_proceeds": 42, "currency_override_note": "Reviewed currency",
        "reinvestment_story": "Mock Data retained story", "company_age": 0,
    })
    assert response.status_code == 201, response.text
    return model, response.json()["data"]


def basis(row):
    return {"base_assumption_set_id": row["id"], "base_assumption_set_updated_at": row["updated_at"]}


def test_sparse_version_preserves_all_omitted_inputs_and_prior_record(client, db_session):
    model, old = saved(client, db_session)
    response = client.post(f"/valuation-models/{model.id}/assumptions", json={**basis(old), "story_text": "New story"})
    assert response.status_code == 201, response.text
    new = response.json()["data"]
    from app.schemas.valuation_inputs import DcfAssumptionSetCreate
    for field in DcfAssumptionSetCreate.model_fields:
        if field not in {"story_text", "is_stale", "stale_reason", "stale_event_id"}:
            assert new[field] == old[field], field
    assert new["id"] != old["id"]
    db_session.expire_all()
    assert db_session.get(DcfAssumptionSet, old["id"]).story_text is None
    logs = db_session.scalars(select(ValuationAssumptionChangeLog).where(
        ValuationAssumptionChangeLog.assumption_set_id == new["id"])).all()
    assert {log.parameter_name for log in logs} == {"story_text"}


def test_explicit_null_clears_and_zero_survives(client, db_session):
    model, old = saved(client, db_session)
    response = client.post(f"/valuation-models/{model.id}/assumptions", json={
        **basis(old), "book_value_of_equity": None, "net_income": 0, "cash": 0,
    })
    assert response.status_code == 201, response.text
    new = response.json()["data"]
    assert new["book_value_of_equity"] is None
    assert new["net_income"] == new["cash"] == 0


@pytest.mark.parametrize("conflict", ["new_version", "changed_timestamp", "wrong_model"])
def test_obsolete_or_wrong_basis_does_not_write(client, db_session, conflict):
    model, old = saved(client, db_session)
    if conflict == "new_version":
        assert client.post(f"/valuation-models/{model.id}/assumptions", json=valid_inputs()).status_code == 201
    elif conflict == "changed_timestamp":
        row = db_session.get(DcfAssumptionSet, old["id"])
        row.is_stale = True
        db_session.commit()
    else:
        model, _ = saved(client, db_session)
    count = db_session.scalar(select(func.count()).select_from(DcfAssumptionSet))
    response = client.post(f"/valuation-models/{model.id}/assumptions", json=basis(old))
    assert response.status_code == 409, response.text
    assert response.json()["errors"][0]["code"] == "VALUATION_VERSION_CONFLICT"
    assert db_session.scalar(select(func.count()).select_from(DcfAssumptionSet)) == count


def test_merged_values_are_validated_and_failure_is_atomic(client, db_session):
    model, old = saved(client, db_session)
    count = db_session.scalar(select(func.count()).select_from(DcfAssumptionSet))
    response = client.post(f"/valuation-models/{model.id}/assumptions", json={
        **basis(old), "discount_rate_currency": "INR", "currency_override_note": None,
    })
    assert response.status_code == 422, response.text
    assert db_session.scalar(select(func.count()).select_from(DcfAssumptionSet)) == count


def test_version_basis_requires_timestamp_and_owner(client, db_session):
    model, old = saved(client, db_session)
    assert client.post(f"/valuation-models/{model.id}/assumptions", json={"base_assumption_set_id": old["id"]}).status_code == 422
    model.user_id = "another-owner"
    db_session.commit()
    assert client.post(f"/valuation-models/{model.id}/assumptions", json=basis(old)).status_code == 404
