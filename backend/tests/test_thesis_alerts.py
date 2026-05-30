import pytest
from fastapi.testclient import TestClient

from app.models import ThesisNote, Company


def test_thesis_assumption_and_change_crud(client: TestClient, db_session):
    # Setup test company and thesis note
    company = Company(ticker="TEST-THESIS", name="Test Thesis")
    db_session.add(company)
    db_session.commit()

    thesis_res = client.post("/api/thesis-notes", json={
        "company_id": company.id,
        "title": "Initial Thesis",
        "thesis_text": "Buy because cheap."
    })
    assert thesis_res.status_code == 201
    thesis_id = thesis_res.json()["id"]

    # Test Create Assumption
    assump_res = client.post(f"/api/thesis-notes/{thesis_id}/assumptions", json={
        "thesis_note_id": thesis_id,
        "description": "Earnings will grow 20%",
        "original_confidence": "high",
        "current_confidence": "high"
    })
    assert assump_res.status_code == 201
    assump_id = assump_res.json()["id"]

    # Test Update Assumption
    up_res = client.patch(f"/api/thesis-assumptions/{assump_id}", json={
        "current_confidence": "low"
    })
    assert up_res.status_code == 200
    assert up_res.json()["current_confidence"] == "low"

    # Test Create Change (Drift)
    change_res = client.post(f"/api/thesis-notes/{thesis_id}/changes", json={
        "thesis_note_id": thesis_id,
        "change_summary": "Earnings miss",
        "drift_score": 0.5
    })
    assert change_res.status_code == 201
    assert change_res.json()["drift_score"] == 0.5

    # Verify drift score accumulated
    get_res = client.get(f"/api/thesis-notes/{thesis_id}")
    assert get_res.status_code == 200
    assert get_res.json()["thesis_drift_score"] == 0.5
    assert len(get_res.json()["assumptions"]) == 1
    assert len(get_res.json()["changes"]) == 1

    # Test Delete Assumption
    del_res = client.delete(f"/api/thesis-assumptions/{assump_id}")
    assert del_res.status_code == 204


def test_list_alerts_owned_only(client: TestClient, db_session):
    # This just tests the API endpoint takes the param and returns 200.
    res = client.get("/api/alerts?owned_only=true")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
