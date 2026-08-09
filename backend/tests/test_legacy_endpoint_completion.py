from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Company, Event
from app.models.thesis_note import EventThesisImpact, ThesisAssumption, ThesisNote
from helpers import response_data


def test_evaluation_runs_are_explicitly_created_but_not_claimed_as_executed(
    client: TestClient,
) -> None:
    created_response = client.post("/evaluations/runs")

    assert created_response.status_code == 201
    created = response_data(created_response)
    assert created["evaluation_type"] == "financial_extraction"
    assert created["status"] == "created"
    assert "not been run" in created_response.json()["meta"]["warnings"][0]

    runs = response_data(client.get("/evaluations/runs"))
    assert [run["id"] for run in runs] == [created["id"]]


def test_thesis_evidence_detection_is_owner_scoped_labeled_and_idempotent(
    client: TestClient,
    db_session: Session,
) -> None:
    company = Company(ticker="EVID", name="Evidence Test")
    db_session.add(company)
    db_session.flush()
    thesis = ThesisNote(
        company_id=company.id,
        title="Growth thesis",
        thesis_text="Revenue growth should persist.",
    )
    event = Event(
        company_id=company.id,
        event_type="earnings",
        information_speed="fast",
        title="Revenue growth beat expectations",
        description="Management reported continued growth.",
    )
    db_session.add_all([thesis, event])
    db_session.flush()
    db_session.add(
        ThesisAssumption(
            thesis_note_id=thesis.id,
            description="Revenue continues to grow.",
        )
    )
    db_session.commit()

    first_response = client.post(
        f"/thesis/{thesis.id}/evidence/detect",
        json={"event_id": event.id},
    )
    second_response = client.post(
        f"/thesis/{thesis.id}/evidence/detect",
        json={"event_id": event.id},
    )

    assert first_response.status_code == 200
    assert first_response.json()["meta"]["is_mock"] is False
    assert response_data(first_response)["claim_type"] == "Calculation"
    assert response_data(first_response)["confirmations"] == []
    assert response_data(first_response)["contradictions"] == []
    assert response_data(second_response)["confirmations"] == response_data(first_response)["confirmations"]
    assert db_session.query(EventThesisImpact).count() == 0
