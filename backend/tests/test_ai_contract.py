import pytest
from sqlalchemy import select

from app.models.ai import AiOutput
from app.providers.base import AIProviderResult, BaseAIProvider
from app.services.ai_contract import (
    AIProvenance,
    AIProviderFailed,
    AIProviderNotConfigured,
    AIPrivacyDisclosureRequired,
    execute_ai_generation,
    require_privacy_disclosure,
    select_ai_provider,
)
from test_ai_consent import decision


class FailingProvider(BaseAIProvider):
    @property
    def provider_name(self) -> str:
        return "gemini"

    def generate_summary(self, text: str) -> AIProviderResult:
        raise RuntimeError("sensitive upstream response")

    def generate_chat_response(self, messages: list[dict], context: str = "") -> AIProviderResult:
        raise RuntimeError("sensitive upstream response")

    def generate_structured_response(self, prompt: str, schema: dict) -> AIProviderResult:
        raise RuntimeError("sensitive upstream response")


def provenance() -> AIProvenance:
    return AIProvenance(
        user_id="admin_user_id_fallback",
        prompt_version="test-v1",
        input_text="private input",
        reference_type="test",
        reference_id=1,
        source_ids=("document:1",),
        source_scope="test_scope",
        external_data_classes=("raw_document_text",),
        action_key="document_summary", privacy_disclosure_version="v1",
    )


def test_unconfigured_provider_requires_explicit_demo_mode(monkeypatch) -> None:
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("AI_DEMO_MODE", raising=False)

    with pytest.raises(AIProviderNotConfigured):
        select_ai_provider()


def test_demo_mode_is_explicitly_mock(monkeypatch) -> None:
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setenv("AI_DEMO_MODE", "true")

    assert select_ai_provider().provider_name == "mock"


def test_privacy_disclosure_version_must_match(monkeypatch) -> None:
    monkeypatch.setenv("AI_PRIVACY_DISCLOSURE_VERSION", "v1")

    require_privacy_disclosure("v1")
    with pytest.raises(AIPrivacyDisclosureRequired):
        require_privacy_disclosure(None)


def test_provider_failure_is_recorded_without_silent_mock_fallback(db_session) -> None:
    grant = decision(db_session)
    with pytest.raises(AIProviderFailed):
        execute_ai_generation(
            db_session,
            provenance=provenance(),
            provider=FailingProvider(),
            generate=lambda provider: provider.generate_summary("private input"),
        )

    stored = db_session.scalar(select(AiOutput))
    assert stored is not None
    assert stored.provider_name == "gemini"
    assert stored.consent_decision_id == grant.id
    assert stored.is_mock is False
    assert stored.execution_status == "failed"
    assert stored.failure_code == "AI_PROVIDER_FAILED"
    assert stored.output_text == ""
    assert "sensitive upstream response" not in (stored.limitations or "")
