import json
from contextlib import contextmanager

import httpx
import pytest
from sqlalchemy import func, select

from app.models import Event
from app.models.ai import AiOutput
from app.providers.base import AIProviderResult


@pytest.mark.parametrize("path,payload", [
    ("map-event-to-dcf", {"event_text": "Mock Data event"}),
    ("summarize", {"document_id": 1, "user_task": "Summarize"}),
    ("questions", {"document_id": 1, "user_question": "What changed?"}),
])
def test_research_ai_requires_disclosure_before_any_provider_call(client, db_session, monkeypatch, path, payload):
    def forbidden():
        raise AssertionError("No provider access without disclosure")
    monkeypatch.setattr("app.services.ai_contract.select_ai_provider", forbidden)
    response = client.post(f"/ai/research/{path}", json=payload)
    assert response.status_code == 409, response.text
    assert db_session.scalar(select(func.count()).select_from(AiOutput)) == 0


@pytest.mark.parametrize("case,status", [("missing",404), ("edited",409), ("oversized",422)])
def test_event_mapping_rejects_missing_stale_or_oversized_input(client, db_session, case, status):
    event = Event(title="Mock Data event", description="Recorded source text", event_type="manual", information_speed="slow")
    db_session.add(event); db_session.commit()
    payload = {"event_id": event.id, "event_text": f"{event.title}\n{event.description}", "privacy_disclosure_version": "v1"}
    if case == "missing": payload["event_id"] = event.id + 999
    if case == "edited": payload["event_text"] = "Mock Data outdated event text"
    if case == "oversized": payload["event_text"] = "x" * 20001
    response = client.post("/ai/research/map-event-to-dcf", json=payload)
    assert response.status_code == status, response.text
    assert db_session.scalar(select(func.count()).select_from(AiOutput)) == 0


def test_event_mapping_retains_provider_source_and_pending_review(client, db_session, monkeypatch):
    event = Event(title="Mock Data event", description="Revenue changed", event_type="manual", information_speed="slow")
    db_session.add(event); db_session.commit()
    from app.services.ai_contract import select_ai_provider
    provider = select_ai_provider()
    monkeypatch.setattr(provider, "generate_structured_response", lambda *_: AIProviderResult(output_text=json.dumps({"impacted_variables":[{
        "variable_name":"Revenue Growth Rate", "impact_direction":"unknown", "confidence":"low", "reasoning":"Mock Data requires source review"}]}), model_name="mock", confidence_label="low", limitations="Mock Data"))
    monkeypatch.setattr("app.services.ai_contract.select_ai_provider", lambda: provider)
    response = client.post("/ai/research/map-event-to-dcf", json={"event_id":event.id,
        "event_text":f"{event.title}\n{event.description}", "privacy_disclosure_version":"v1"})
    assert response.status_code == 200, response.text
    output = response.json()["data"]["ai_output"]
    assert output["human_review_status"] == "pending"
    assert output["source_ids_json"] == [f"event:{event.id}"]
    assert output["external_data_classes_json"] == ["event_text"]
    assert output["source_scope"] == "provided_event_text"
    assert len(output["input_hash"]) == 64 and output["prompt_version"] and output["created_at"]
    assert output["is_mock"] is True
    assert output["is_blocked"] is True
    assert output["evaluation_json"]["interpretation_quality"] == "not_evaluated"


def test_event_mapping_uses_actual_mock_provider_schema(client):
    response = client.post("/ai/research/map-event-to-dcf", json={
        "event_text": "Mock Data demo event", "privacy_disclosure_version": "v1"})
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["impacted_variables"] == []
    assert data["ai_output"]["is_mock"] is True
    assert data["ai_output"]["human_review_status"] == "pending"


def test_event_mapping_sends_inline_schema_through_real_gemini_transport(client, monkeypatch):
    from app.providers import ai_provider

    captured = {}
    interpretation = {"impacted_variables": [{
        "variable_name": "Revenue Growth Rate", "impact_direction": "unknown",
        "confidence": "low", "reasoning": "Mock Data transport fixture requires review",
    }]}

    class Client:
        def __init__(self, **kwargs):
            captured["client_options"] = kwargs

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            pass

        @contextmanager
        def stream(self, method, url, **kwargs):
            captured["payload"] = kwargs["json"]
            yield httpx.Response(200, request=httpx.Request(method, url), json={
                "candidates": [{"finishReason": "STOP", "content": {
                    "parts": [{"text": json.dumps(interpretation)}],
                }}],
            })

    monkeypatch.setattr(ai_provider.httpx, "Client", Client)
    monkeypatch.setattr("app.services.ai_contract.select_ai_provider",
                        lambda: ai_provider.GeminiAIProvider("mock-transport-key"))
    response = client.post("/ai/research/map-event-to-dcf", json={
        "event_text": "Mock Data transport fixture", "privacy_disclosure_version": "v1",
    })
    assert response.status_code == 200, response.text
    assert response.json()["data"]["impacted_variables"] == interpretation["impacted_variables"]
    config = captured["payload"]["generationConfig"]
    assert config["responseMimeType"] == "application/json"
    schema = config["responseSchema"]
    # responseSchema accepts inline OpenAPI schemas, not JSON Schema references.
    serialized = json.dumps(schema)
    assert '"$defs"' not in serialized and '"$ref"' not in serialized
    assert schema["type"] == "OBJECT"
    assert schema["required"] == ["impacted_variables"]
    impacts = schema["properties"]["impacted_variables"]
    assert impacts["type"] == "ARRAY" and impacts["maxItems"] == 20
    item = impacts["items"]
    assert item["type"] == "OBJECT"
    assert set(item["required"]) == {"variable_name", "impact_direction", "confidence", "reasoning"}
    fields = item["properties"]
    assert all(field["type"] == "STRING" for field in fields.values())
    assert fields["impact_direction"]["enum"] == ["increase", "decrease", "unknown"]
    assert fields["confidence"]["enum"] == ["high", "medium", "low"]
    assert fields["variable_name"]["minLength"] == fields["reasoning"]["minLength"] == 1
    assert fields["variable_name"]["maxLength"] == 150
    assert fields["reasoning"]["maxLength"] == 2000


@pytest.mark.parametrize("unsafe_field", ["reasoning", "variable_name"])
def test_recommendation_text_is_rejected_and_audited(client, db_session, monkeypatch, unsafe_field):
    from app.services.ai_contract import select_ai_provider
    provider = select_ai_provider()
    impact = {"variable_name": "Revenue Growth Rate", "impact_direction": "unknown",
              "confidence": "low", "reasoning": "Mock Data interpretation"}
    impact[unsafe_field] = "You should buy this stock; guaranteed upside"
    monkeypatch.setattr(provider, "generate_structured_response", lambda *_: AIProviderResult(
        output_text=json.dumps({"impacted_variables": [impact]}), model_name="mock",
        confidence_label="low", limitations="Mock Data"))
    monkeypatch.setattr("app.services.ai_contract.select_ai_provider", lambda: provider)
    response = client.post("/ai/research/map-event-to-dcf", json={
        "event_text": "Mock Data event", "privacy_disclosure_version": "v1"})
    assert response.status_code == 502, response.text
    output = db_session.scalar(select(AiOutput))
    assert output.execution_status == "failed" and output.is_blocked
    assert output.failure_code == "AI_OUTPUT_INVALID"
    assert output.evaluation_json["checks"]["no_recommendation_language"] is False
    assert output.evaluation_json["interpretation_quality"] == "not_evaluated"


def test_malformed_event_mapping_is_a_failed_audited_output(client, db_session, monkeypatch):
    from app.services.ai_contract import select_ai_provider
    provider = select_ai_provider()
    monkeypatch.setattr(provider, "generate_structured_response", lambda *_: AIProviderResult(output_text='{"impacted_variables":[{"confidence":"guaranteed"}]}', model_name="mock", confidence_label="low", limitations="Mock Data"))
    monkeypatch.setattr("app.services.ai_contract.select_ai_provider", lambda: provider)
    response = client.post("/ai/research/map-event-to-dcf", json={"event_text":"Mock Data event", "privacy_disclosure_version":"v1"})
    assert response.status_code == 502, response.text
    output = db_session.scalar(select(AiOutput))
    assert output.execution_status == "failed" and output.is_blocked
    assert output.failure_code == "AI_OUTPUT_INVALID"
