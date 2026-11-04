"""Permission UI contracts and real route enforcement, with no network transport."""
from sqlalchemy import select

from app.api.dependencies import get_current_user
from app.main import app
from app.models.ai import AiOutput
from app.models.ai_consent import AiConsentDecision
from app.models.research import ResearchMessage
from app.models.raw_document import RawDocument
from test_ai_consent import RecordingProvider


def allow(client, action_key, state="granted"):
    action = next(item for item in client.get("/ai/consent").json()["data"]["actions"] if item["action_key"] == action_key)
    return client.post("/ai/consent/decisions", json={"provider_name": action["provider_name"],
        "action_key": action_key, "state": state, "disclosure_version": action["disclosure_version"],
        "scope_hash": action["scope_hash"], "expected_revision": action["current_revision"]})


def test_permission_reads_and_owner_history_are_isolated(client, db_session, monkeypatch):
    def forbidden():
        raise AssertionError("Permission management selected a provider")
    monkeypatch.setattr("app.services.ai_contract.select_ai_provider", forbidden)
    assert client.get("/ai/consent").status_code == 200
    assert client.get("/ai/consent/history").json()["data"] == {"items": [], "next_cursor": None}
    assert db_session.scalar(select(AiConsentDecision)) is None
    assert allow(client, "document_summary").status_code == 200
    assert allow(client, "document_summary", "revoked").status_code == 200
    history = client.get("/ai/consent/history?limit=1").json()["data"]
    assert len(history["items"]) == 1 and history["next_cursor"]
    app.dependency_overrides[get_current_user] = lambda: {"id": "another-owner"}
    assert {row["state"] for row in client.get("/ai/consent").json()["data"]["actions"]} == {"not_granted"}
    assert client.get("/ai/consent/history").json()["data"]["items"] == []


def test_scope_forgery_stale_revision_and_invalid_pagination_fail(client, db_session):
    action = client.get("/ai/consent").json()["data"]["actions"][0]
    payload = {"provider_name": "gemini", "action_key": action["action_key"], "state": "granted",
        "disclosure_version": "v1", "scope_hash": action["scope_hash"], "expected_revision": 0}
    assert client.post("/ai/consent/decisions", json={**payload, "user_id": "someone"}).status_code == 422
    assert client.post("/ai/consent/decisions", json={**payload, "scope_hash": "0" * 64}).status_code == 409
    assert client.post("/ai/consent/decisions", json={**payload, "action_key": "thesis_contradiction"}).status_code == 422
    assert client.post("/ai/consent/decisions", json=payload).status_code == 200
    assert client.post("/ai/consent/decisions", json={**payload, "state": "revoked"}).status_code == 409
    assert client.get("/ai/consent/history?limit=101").status_code == 422
    assert client.get("/ai/consent/history?cursor=0").status_code == 422
    assert db_session.query(AiConsentDecision).count() == 1


def test_document_route_blocks_then_links_grant_and_rejects_revocation(client, db_session, monkeypatch):
    source = client.post("/sources", json={"name": "Mock Data permission source", "source_type": "manual"}).json()["data"]
    document = RawDocument(source_id=source["id"], document_type="manual_note", title="Mock Data consent fixture", raw_text="Mock Data text",
                           content_hash="consent-route-source")
    db_session.add(document); db_session.commit()
    provider = RecordingProvider()
    monkeypatch.setattr("app.services.ai_contract.select_ai_provider", lambda: provider)
    path = f"/raw-documents/{document.id}/ai-summary"
    assert client.post(path, json={"privacy_disclosure_version": "v1"}).status_code == 409
    assert not provider.calls
    grant = allow(client, "document_summary").json()["data"]
    result = client.post(path, json={"privacy_disclosure_version": "v1"})
    assert result.status_code == 200, result.text
    assert result.json()["data"]["consent_decision_id"] == grant["id"]
    assert allow(client, "document_summary", "revoked").status_code == 200
    assert client.post(path, json={"privacy_disclosure_version": "v1"}).status_code == 409
    assert len(provider.calls) == 1
    assert client.get(f"/raw-documents/{document.id}/ai-outputs").status_code == 200
    assert len(provider.calls) == 1


def test_research_refusal_precedes_message_write_and_snippets_are_disclosed(client, db_session, monkeypatch):
    session = client.post("/research/sessions", json={"title": "Mock Data consent chat"}).json()["data"]
    source = client.post("/sources", json={"name": "Mock Data chat source", "source_type": "manual"}).json()["data"]
    document = RawDocument(source_id=source["id"], document_type="manual_note", title="Mock Data excerpt title", raw_text="Mock Data selected excerpt",
                           content_hash="consent-chat-excerpt")
    db_session.add(document); db_session.commit()
    provider = RecordingProvider()
    monkeypatch.setattr("app.api.routers.research.select_ai_provider", lambda: provider)
    monkeypatch.setattr("app.api.routers.research.search_evidence", lambda *args, **kwargs: [{"record_id": document.id}])
    path = f"/research/sessions/{session['id']}/messages"
    payload = {"role": "user", "content": "Mock Data question", "privacy_disclosure_version": "v1"}
    assert client.post(path, json=payload).status_code == 409
    assert db_session.query(ResearchMessage).count() == 0 and not provider.calls
    assert allow(client, "research_chat").status_code == 200
    result = client.post(path, json=payload)
    assert result.status_code == 200, result.text
    output = db_session.scalar(select(AiOutput))
    assert output.external_data_classes_json == ["private_research_messages", "retrieved_document_excerpts"]
    assert "Mock Data selected excerpt" in provider.calls[0]
    assert client.get(f"/research/sessions/{session['id']}").status_code == 200
    assert len(provider.calls) == 1
