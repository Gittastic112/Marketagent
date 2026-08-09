import pytest
from fastapi.testclient import TestClient

from app.models import ThesisNote, Company
from helpers import response_data


def test_thesis_assumption_and_change_crud(client: TestClient, db_session):
    # Setup test company and thesis note
    company = Company(ticker="TEST-THESIS", name="Test Thesis")
    db_session.add(company)
    db_session.commit()

    thesis_res = client.post("/thesis-notes", json={
        "company_id": company.id,
        "title": "Initial Thesis",
        "thesis_text": "Buy because cheap."
    })
    assert thesis_res.status_code == 201
    thesis_id = response_data(thesis_res)["id"]

    # Test Create Assumption
    assump_res = client.post(f"/thesis-notes/{thesis_id}/assumptions", json={
        "thesis_note_id": thesis_id,
        "description": "Earnings will grow 20%",
        "original_confidence": "high",
        "current_confidence": "high"
    })
    assert assump_res.status_code == 201
    assump_id = response_data(assump_res)["id"]

    # Test Update Assumption
    up_res = client.patch(f"/thesis-assumptions/{assump_id}", json={
        "current_confidence": "low"
    })
    assert up_res.status_code == 200
    assert response_data(up_res)["current_confidence"] == "low"

    # Test Create Change (Drift)
    change_res = client.post(f"/thesis-notes/{thesis_id}/changes", json={
        "thesis_note_id": thesis_id,
        "change_summary": "Earnings miss",
        "drift_score": 0.5
    })
    assert change_res.status_code == 201
    assert response_data(change_res)["drift_score"] == 0.5

    # Verify drift score accumulated
    get_res = client.get(f"/thesis-notes/{thesis_id}")
    assert get_res.status_code == 200
    thesis = response_data(get_res)
    assert thesis["thesis_drift_score"] == 0.5
    assert len(thesis["assumptions"]) == 1
    assert len(thesis["changes"]) == 1

    # Test Delete Assumption
    del_res = client.delete(f"/thesis-assumptions/{assump_id}")
    assert del_res.status_code == 204


def test_list_alerts_owned_only(client: TestClient, db_session):
    # This just tests the API endpoint takes the param and returns 200.
    res = client.get("/alerts?owned_only=true")
    assert res.status_code == 200
    assert isinstance(response_data(res), list)
