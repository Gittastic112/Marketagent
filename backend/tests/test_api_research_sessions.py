from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.main import app
from app.models.research import ResearchMessage, ResearchSession
from app.models.ai import AiOutput
from helpers import response_data


def use_user(user_id: str) -> None:
    app.dependency_overrides[get_current_user] = lambda: {
        "id": user_id,
        "email": f"{user_id}@example.com",
        "name": user_id,
    }


def test_research_session_creation_persists_authenticated_owner(
    client: TestClient,
    db_session: Session,
) -> None:
    created = response_data(
        client.post("/research/sessions", json={"title": "Owned research"})
    )

    stored = db_session.get(ResearchSession, created["id"])
    assert stored is not None
    assert stored.user_id == "admin_user_id_fallback"


def test_research_session_children_resolve_through_owned_parent(
    client: TestClient,
    db_session: Session,
) -> None:
    created = response_data(
        client.post("/research/sessions", json={"title": "Private research"})
    )

    use_user("other-user")

    assert response_data(client.get("/research/sessions")) == []
    assert client.get(f"/research/sessions/{created['id']}").status_code == 404
    assert client.post(
        f"/research/sessions/{created['id']}/messages",
        json={
            "role": "user",
            "content": "Attempted cross-user write",
            "privacy_disclosure_version": "v1",
        },
    ).status_code == 404
    assert client.delete(f"/research/sessions/{created['id']}").status_code == 404
    assert db_session.query(ResearchMessage).count() == 0


def test_research_messages_reject_caller_supplied_assistant_role(
    client: TestClient,
) -> None:
    created = response_data(
        client.post("/research/sessions", json={"title": "Typed messages"})
    )

    response = client.post(
        f"/research/sessions/{created['id']}/messages",
        json={"role": "assistant", "content": "Caller supplied output"},
    )

    assert response.status_code == 422


def test_research_ai_response_is_explicitly_mock_and_provenanced(
    client: TestClient,
    db_session: Session,
) -> None:
    created = response_data(
        client.post("/research/sessions", json={"title": "Provenance test"})
    )

    response = client.post(
        f"/research/sessions/{created['id']}/messages",
        json={
            "role": "user",
            "content": "What evidence is available?",
            "privacy_disclosure_version": "v1",
        },
    )

    assert response.status_code == 200
    assert response.json()["meta"]["is_mock"] is True
    assert response.json()["meta"]["warnings"] == ["Mock Data"]
    output = db_session.query(AiOutput).one()
    assert output.user_id == "admin_user_id_fallback"
    assert output.reference_type == "research_session"
    assert output.reference_id == created["id"]
    assert output.external_data_classes_json == ["private_research_messages"]
    assert output.transmission_scope == "none"


def test_research_session_owner_can_delete_session_and_messages(
    client: TestClient,
    db_session: Session,
) -> None:
    created = response_data(
        client.post("/research/sessions", json={"title": "Disposable research"})
    )
    session = db_session.get(ResearchSession, created["id"])
    assert session is not None
    db_session.add(
        ResearchMessage(
            session_id=session.id,
            role="user",
            content="Stored question",
        )
    )
    db_session.commit()

    response = client.delete(f"/research/sessions/{created['id']}")

    assert response.status_code == 204
    assert db_session.get(ResearchSession, created["id"]) is None
    assert db_session.query(ResearchMessage).count() == 0
def test_session_exposes_own_pending_attempts_for_reconciliation(client, db_session):
    from app.models.ai import AiOutput
    from app.models.user import User
    from conftest import TEST_USER_ID
    session = client.post("/research/sessions", json={"title": "Mock Data interrupted chat"}).json()["data"]
    db_session.add(User(id="other-attempt", email="other-attempt@example.invalid", name="Other"))
    db_session.flush()
    for owner in [TEST_USER_ID, "other-attempt"]:
        db_session.add(AiOutput(user_id=owner, reference_type="research_session", reference_id=session["id"],
            provider_name="mock", model_name="test", is_mock=True, prompt_version="test", input_hash="test",
            output_text="", confidence_label="none", execution_status="pending", transmission_scope="none"))
    db_session.commit()
    detail = client.get(f"/research/sessions/{session['id']}").json()["data"]
    assert len(detail["attempts"]) == 1
    assert detail["attempts"][0]["execution_status"] == "pending"
    assert detail["messages"] == []
