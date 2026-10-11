import pytest
import httpx
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


@pytest.mark.parametrize("operation", ["summary", "chat", "structured"])
def test_gemini_uses_header_auth_and_configured_model(monkeypatch, operation):
    calls = []

    def post(url, **kwargs):
        calls.append((url, kwargs))
        return httpx.Response(200, request=httpx.Request("POST", url), json={
            "candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": "answer"}]}}],
        })

    monkeypatch.setattr("app.providers.ai_provider.httpx.post", post)
    provider = GeminiAIProvider(api_key="test-key", model_name="gemini-test-flash")
    if operation == "summary":
        result = provider.generate_summary("document")
    elif operation == "chat":
        result = provider.generate_chat_response([{"role": "user", "content": "question"}])
    else:
        result = provider.generate_structured_response("prompt", {"type": "OBJECT"})
    assert result.model_name == "gemini-test-flash"
    url, kwargs = calls[0]
    assert url.endswith("/models/gemini-test-flash:generateContent")
    assert "test-key" not in url and "?" not in url
    assert kwargs["headers"]["x-goog-api-key"] == "test-key"
    assert kwargs["timeout"] == 30.0


@pytest.mark.parametrize("model", ["../escape", "gemini-a?key=bad", "https://elsewhere/model", ""])
def test_gemini_rejects_invalid_model_ids(model):
    with pytest.raises(ValueError, match="model"):
        GeminiAIProvider(api_key="test-key", model_name=model)


def test_gemini_reads_all_public_text_parts_without_thoughts(monkeypatch):
    response = httpx.Response(200, request=httpx.Request("POST", "https://example.invalid"), json={
        "candidates": [{"finishReason": "STOP", "content": {"parts": [
            {"text": "internal reasoning", "thought": True},
            {"text": "first "}, {"text": "second"},
        ]}}],
    })
    monkeypatch.setattr("app.providers.ai_provider.httpx.post", lambda *a, **k: response)
    assert GeminiAIProvider("test-key").generate_summary("document").output_text == "first second"


def test_gemini_rejects_truncated_text(monkeypatch):
    response = httpx.Response(200, request=httpx.Request("POST", "https://example.invalid"), json={
        "candidates": [{"finishReason": "MAX_TOKENS", "content": {"parts": [{"text": "partial"}]}}],
    })
    monkeypatch.setattr("app.providers.ai_provider.httpx.post", lambda *a, **k: response)
    with pytest.raises(RuntimeError):
        GeminiAIProvider("test-key").generate_summary("document")


def test_gemini_failures_do_not_retain_secret_exception_context(monkeypatch, caplog):
    def fail(*a, **k):
        raise RuntimeError("test-key private document")
    monkeypatch.setattr("app.providers.ai_provider.httpx.post", fail)
    with pytest.raises(RuntimeError) as error:
        GeminiAIProvider("test-key").generate_summary("private document")
    assert "test-key" not in str(error.value)
    assert error.value.__suppress_context__ is True
    assert "test-key" not in caplog.text and "private document" not in caplog.text
