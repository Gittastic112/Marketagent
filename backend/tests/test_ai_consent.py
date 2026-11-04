"""No external callback without a current, explicit owner/action/provider grant."""
from dataclasses import replace
import json

import pytest
from sqlalchemy import select

from app.models.ai import AiOutput
from app.models.ai_consent import AiConsentDecision
from app.models.user import User
from app.providers.base import AIProviderResult, BaseAIProvider
from app.providers.mock_provider import MockAIProvider
from app.schemas.ai_consent import AIConsentDecisionRequest
from app.services.ai_consent import (
    ACTIONS, ACTION_BY_KEY, ConsentPolicyError, action_scope_hash, consent_history,
    consent_overview, record_decision,
)
from app.services.ai_contract import AIExecutionError, AIProvenance, execute_ai_generation, require_provider_consent


OWNER = "admin_user_id_fallback"


class RecordingProvider(BaseAIProvider):
    """Transport-free test double. Never opens a connection."""
    provider_name = "gemini"

    def __init__(self):
        self.calls = []

    def generate_summary(self, text):
        self.calls.append(text)
        return AIProviderResult(model_name="test-recording", output_text="Mock Data transport-free response",
            limitations="Test double; no provider contacted.", confidence_label="low")

    def generate_chat_response(self, messages, context=""):
        return self.generate_summary(str(messages))

    def generate_structured_response(self, prompt, schema):
        return self.generate_summary(prompt)


def decision(db, action_key="document_summary", state="granted", revision=0, user_id=OWNER):
    action = ACTION_BY_KEY[action_key]
    return record_decision(db, user_id, AIConsentDecisionRequest(provider_name="gemini", action_key=action_key,
        state=state, disclosure_version="v1", scope_hash=action_scope_hash(action), expected_revision=revision))


def provenance(action_key="document_summary", **changes):
    data = AIProvenance(user_id=OWNER, prompt_version="consent-test-v1", input_text="Mock Data test input",
        action_key=action_key, privacy_disclosure_version="v1",
        external_data_classes=ACTION_BY_KEY[action_key].data_classes)
    return replace(data, **changes)


def execute(db, provider, data):
    return execute_ai_generation(db, provider=provider, provenance=data,
        generate=lambda selected: selected.generate_summary("Mock Data test input"))


@pytest.mark.parametrize("action", ACTIONS, ids=lambda action: action.key)
def test_each_available_action_denies_without_grant_and_retains_exact_grant_when_allowed(db_session, action):
    provider = RecordingProvider()
    with pytest.raises(AIExecutionError) as denied:
        execute(db_session, provider, provenance(action.key))
    assert denied.value.code == "AI_CONSENT_REQUIRED"
    assert provider.calls == []
    failure = db_session.scalar(select(AiOutput))
    assert failure.transmission_scope == "none" and failure.consent_decision_id is None
    grant = decision(db_session, action.key)
    output = execute(db_session, provider, provenance(action.key))
    assert len(provider.calls) == 1
    assert output.consent_decision_id == grant.id
    assert output.external_data_classes_json == list(action.data_classes)
    assert output.human_review_status == "pending"


@pytest.mark.parametrize("state", ["refused", "revoked"])
def test_latest_refusal_or_revocation_blocks_even_after_prior_generation(db_session, state):
    provider = RecordingProvider()
    grant = decision(db_session)
    historical = execute(db_session, provider, provenance())
    decision(db_session, state=state, revision=1)
    with pytest.raises(AIExecutionError):
        execute(db_session, provider, provenance())
    assert len(provider.calls) == 1
    assert historical.consent_decision_id == grant.id
    renewed = decision(db_session, revision=2)
    assert execute(db_session, provider, provenance()).consent_decision_id == renewed.id
    assert [row.state for row in consent_history(db_session, OWNER).items] == ["granted", state, "granted"]


@pytest.mark.parametrize("change", ["version", "scope", "acknowledgement", "extra_data", "owner", "provider", "unknown_action", "spoof_mock"])
def test_changed_scope_identity_or_acknowledgement_never_calls_provider(db_session, monkeypatch, change):
    decision(db_session)
    provider = RecordingProvider()
    data = provenance()
    if change == "version":
        monkeypatch.setenv("AI_PRIVACY_DISCLOSURE_VERSION", "v2")
        data = replace(data, privacy_disclosure_version="v2")
    elif change == "scope":
        action = ACTION_BY_KEY["document_summary"]
        monkeypatch.setitem(ACTION_BY_KEY, action.key, replace(action, description=action.description + " Changed scope."))
    elif change == "acknowledgement":
        data = replace(data, privacy_disclosure_version=None)
    elif change == "extra_data":
        data = replace(data, external_data_classes=("raw_document_text", "private_portfolio"))
    elif change == "owner":
        db_session.add(User(id="other", email="other@example.test")); db_session.commit()
        data = replace(data, user_id="other")
    elif change == "provider":
        provider.provider_name = "unapproved-provider"
    elif change == "unknown_action":
        data = replace(data, action_key="thesis_contradiction")
    else:
        provider.provider_name = "mock"
    with pytest.raises(AIExecutionError):
        execute(db_session, provider, data)
    assert provider.calls == []


def test_revocation_between_preflight_and_execution_is_observed(db_session):
    decision(db_session)
    provider = RecordingProvider()
    require_provider_consent(db_session, provider=provider, provenance=provenance())
    decision(db_session, state="revoked", revision=1)
    with pytest.raises(AIExecutionError):
        execute(db_session, provider, provenance())
    assert not provider.calls


def test_mock_is_local_and_never_creates_permission(db_session):
    output = execute(db_session, MockAIProvider(), provenance(privacy_disclosure_version=None))
    assert output.is_mock and output.transmission_scope == "none" and output.consent_decision_id is None
    assert db_session.scalar(select(AiConsentDecision)) is None


def test_reads_do_not_infer_permissions_from_historical_outputs(db_session):
    execute(db_session, MockAIProvider(), provenance())
    for _ in range(2):
        assert {item.state for item in consent_overview(db_session, OWNER).actions} == {"not_granted"}
        assert consent_history(db_session, OWNER).items == []
    assert db_session.scalar(select(AiConsentDecision)) is None


def test_stale_decision_cannot_overwrite_current_permission(db_session):
    decision(db_session)
    with pytest.raises(ConsentPolicyError) as conflict:
        decision(db_session, state="revoked", revision=0)
    assert conflict.value.code == "AI_CONSENT_CONFLICT"
    assert len(consent_history(db_session, OWNER).items) == 1


def test_optional_retrieval_scope_is_bounded_and_history_is_paginated(db_session):
    provider = RecordingProvider()
    decision(db_session, "research_chat")
    execute(db_session, provider, provenance("research_chat", external_data_classes=("private_research_messages",)))
    for revision in range(1, 5):
        decision(db_session, "research_chat", state="revoked" if revision % 2 else "granted", revision=revision)
    first = consent_history(db_session, OWNER, limit=2)
    second = consent_history(db_session, OWNER, limit=2, cursor=first.next_cursor)
    assert len(first.items) == len(second.items) == 2
    assert not {row.id for row in first.items} & {row.id for row in second.items}


def test_batch_extraction_rechecks_revocation_before_each_event(db_session, monkeypatch):
    from app.models.event import Event
    from app.models.narrative import NarrativeMention
    from app.services.narrative_extraction import extract_narratives_from_events

    decision(db_session, "narrative_extraction")
    db_session.add_all([Event(title=f"Mock Data consent batch {index}", event_type="manual", information_speed="slow")
                        for index in range(2)])
    db_session.commit()
    provider = RecordingProvider()

    def generate(prompt, schema):
        provider.calls.append(prompt)
        decision(db_session, "narrative_extraction", state="revoked", revision=1)
        return AIProviderResult(model_name="recording-test", output_text=json.dumps({
            "cluster_name": "Mock Data consent batch", "claim_text": "Mock Data claim", "context_text": "Mock Data context"}),
            limitations="No network.", confidence_label="low")

    monkeypatch.setattr(provider, "generate_structured_response", generate)
    monkeypatch.setattr("app.services.ai_contract.select_ai_provider", lambda: provider)
    with pytest.raises(AIExecutionError):
        extract_narratives_from_events(db_session, user_id=OWNER, privacy_disclosure_version="v1")
    assert len(provider.calls) == 1
    assert db_session.query(NarrativeMention).count() == 1
