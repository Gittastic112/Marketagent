from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.main import app
from app.models.dcf import DcfAssumptionSet, ValuationModel
from helpers import response_data


def use_user(user_id: str) -> None:
    app.dependency_overrides[get_current_user] = lambda: {
        "id": user_id,
        "email": f"{user_id}@example.com",
        "name": user_id,
    }


def create_company(client: TestClient) -> dict:
    return response_data(
        client.post(
            "/companies",
            json={
                "ticker": "OWNR",
                "name": "Ownership Test Corp",
                "market": "US",
                "primary_exchange": "NYSE",
                "local_symbol": "OWNR",
            },
        )
    )


def test_thesis_assumption_review_fields_survive_edits_and_remain_owned(client: TestClient) -> None:
    company = create_company(client)
    note = response_data(client.post("/thesis-notes", json={
        "company_id": company["id"], "title": "Mock Data thesis",
        "thesis_text": "Mock Data review criteria",
    }))
    criteria = {"category": "Profitability", "importance": "high",
                "falsification_trigger": "Two annual periods below the stated margin threshold."}
    assumption = response_data(client.post(f"/thesis-notes/{note['id']}/assumptions", json={
        "thesis_note_id": note["id"], "description": "Mock Data margin assumption", **criteria,
    }))
    for field, value in criteria.items():
        assert assumption[field] == value
    updated = response_data(client.patch(f"/thesis-assumptions/{assumption['id']}",
                                         json={"current_confidence": "low"}))
    for field, value in criteria.items():
        assert updated[field] == value
    read = response_data(client.get(f"/thesis-notes/{note['id']}"))["assumptions"][0]
    assert read["falsification_trigger"] == criteria["falsification_trigger"]
    cleared = response_data(client.patch(f"/thesis-assumptions/{assumption['id']}",
                                         json={"category": None, "falsification_trigger": None}))
    assert cleared["category"] is None and cleared["falsification_trigger"] is None
    assert cleared["importance"] == "high"
    use_user("other-user")
    assert client.patch(f"/thesis-assumptions/{assumption['id']}", json=criteria).status_code == 404


def test_company_thesis_filter_keeps_company_and_owner_scope(client: TestClient) -> None:
    company = create_company(client)
    other = response_data(client.post("/companies", json={"ticker": "OTHER", "name": "Mock Data other company"}))
    for identity in [company["id"], other["id"]]:
        response_data(client.post("/thesis-notes", json={"company_id": identity,
            "title": "Mock Data scoped thesis", "thesis_text": "Keep company and owner scope"}))
    notes = response_data(client.get("/thesis-notes", params={"company_id": company["id"]}))
    assert len(notes) == 1 and notes[0]["company_id"] == company["id"]
    use_user("other-user")
    assert response_data(client.get("/thesis-notes", params={"company_id": company["id"]})) == []


def test_thesis_child_routes_enforce_parent_ownership(client: TestClient) -> None:
    company = create_company(client)
    event = response_data(
        client.post(
            "/events",
            json={
                "company_id": company["id"],
                "event_type": "manual_event",
                "information_speed": "medium",
                "title": "Ownership test event",
            },
        )
    )
    note = response_data(
        client.post(
            "/thesis-notes",
            json={
                "company_id": company["id"],
                "title": "Owned thesis",
                "thesis_text": "Only the owner may modify child records.",
            },
        )
    )
    assumption = response_data(
        client.post(
            f"/thesis-notes/{note['id']}/assumptions",
            json={
                "thesis_note_id": note["id"],
                "description": "Owned assumption",
            },
        )
    )
    impact = response_data(
        client.post(
            f"/thesis-assumptions/{assumption['id']}/impacts",
            json={
                "event_id": event["id"],
                "thesis_assumption_id": assumption["id"],
                "impact_classification": "Supports",
                "rationale": "Owned rationale",
            },
        )
    )

    use_user("other-user")

    assert client.patch(
        f"/thesis-assumptions/{assumption['id']}",
        json={"description": "Unauthorized edit"},
    ).status_code == 404
    assert client.delete(f"/thesis-assumptions/{assumption['id']}").status_code == 404
    assert client.get(f"/thesis-assumptions/{assumption['id']}/impacts").status_code == 404
    assert client.post(
        f"/thesis-assumptions/{assumption['id']}/impacts",
        json={
            "event_id": event["id"],
            "thesis_assumption_id": assumption["id"],
            "impact_classification": "Weakens",
            "rationale": "Unauthorized impact",
        },
    ).status_code == 404
    assert client.delete(f"/thesis-impacts/{impact['id']}").status_code == 404


def test_valuation_model_and_child_routes_enforce_parent_ownership(
    client: TestClient,
    db_session: Session,
) -> None:
    company = create_company(client)
    model = response_data(
        client.post(
            f"/companies/{company['id']}/valuation-models",
            json={
                "company_id": company["id"],
                "name": "Owned valuation",
            },
        )
    )
    stored_model = db_session.get(ValuationModel, model["id"])
    assert stored_model is not None
    assert stored_model.user_id == "admin_user_id_fallback"

    assumption_set = DcfAssumptionSet(
        valuation_model_id=stored_model.id,
        scenario="Base",
        starting_revenue=100.0,
        diluted_shares=10.0,
    )
    db_session.add(assumption_set)
    db_session.commit()

    use_user("other-user")

    models = response_data(client.get(f"/companies/{company['id']}/valuation-models"))
    assert models == []
    assert client.get(f"/valuation-models/{model['id']}/assumptions").status_code == 404
    assert client.post(
        f"/valuation-models/{model['id']}/assumptions",
        json={"scenario": "Base"},
    ).status_code == 404
    assert client.get(
        f"/valuation-models/{model['id']}/assumptions/{assumption_set.id}/forecast"
    ).status_code == 404
    assert client.post(
        f"/valuation-models/{model['id']}/assumptions/{assumption_set.id}/resolve-stale"
    ).status_code == 404
    assert client.get(
        f"/valuation-models/{model['id']}/assumptions/{assumption_set.id}/change-logs"
    ).status_code == 404
    assert client.post(
        f"/valuation-models/{model['id']}/assumptions/{assumption_set.id}/change-logs",
        json={
            "valuation_model_id": model["id"],
            "assumption_set_id": assumption_set.id,
            "parameter_name": "wacc_start",
        },
    ).status_code == 404
    assert client.post(
        "/dcf/reverse",
        json={
            "assumption_set_id": assumption_set.id,
            "target_parameter": "target_operating_margin",
            "current_market_price": 10.0,
        },
    ).status_code == 404
    assert client.delete(f"/valuation-models/{model['id']}").status_code == 404
    assert client.get(
        f"/valuation/{model['id']}/scenarios/Base/ai/memo"
    ).status_code == 404
    assert client.post(
        f"/valuation/{model['id']}/scenarios/Base/ai/memo",
        json={"privacy_disclosure_version": "v1"},
    ).status_code == 404
    assert client.post(
        f"/valuation/{model['id']}/scenarios/Base/ai/narrative-to-numbers",
        json={
            "narrative_text": "Unauthorized private narrative",
            "privacy_disclosure_version": "v1",
        },
    ).status_code == 404
    assert client.post(
        f"/valuations/{model['id']}/select-method",
        json={
            "assumption_key": "equity_risk_premium",
            "method_key": "user_custom",
            "applied_value": 0.05,
            "source_label": "Unauthorized override",
            "confidence": "low",
        },
    ).status_code == 404
