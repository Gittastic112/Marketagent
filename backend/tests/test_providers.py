import pytest
from app.providers.mock_provider import MockAIProvider
from app.providers.ai_provider import GeminiAIProvider

def test_mock_provider():
    provider = MockAIProvider()
    result = provider.generate_summary("test text")

    assert provider.provider_name == "mock"
    assert result.model_name == "mock-model"
    assert "Mock Data: AI Summary" in result.output_text
    assert result.confidence_label == "High (Deterministic)"

def test_gemini_provider_init():
    provider = GeminiAIProvider(api_key="test-key")
    assert provider.provider_name == "gemini"
    assert provider.api_key == "test-key"


def test_gemini_provider_rejects_empty_provider_response(monkeypatch):
    class EmptyResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"candidates": []}

    monkeypatch.setattr("app.providers.ai_provider.httpx.post", lambda *args, **kwargs: EmptyResponse())

    with pytest.raises(RuntimeError, match="AI summary request failed"):
        GeminiAIProvider(api_key="test-key").generate_summary("private text")
