import pytest
import httpx
from contextlib import contextmanager
from app.providers.mock_provider import MockAIProvider
from app.providers.ai_provider import GeminiAIProvider

def stub_stream(monkeypatch, post):
    class Client:
        def __init__(self, **kwargs): self.options = kwargs
        def __enter__(self): return self
        def __exit__(self, *_args): pass
        @contextmanager
        def stream(self, method, url, **kwargs):
            assert method == "POST"
            assert not self.options["trust_env"] and not self.options["follow_redirects"]
            yield post(url, timeout=self.options["timeout"], **kwargs)
    monkeypatch.setattr("app.providers.ai_provider.httpx.Client", Client)

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
    stub_stream(monkeypatch, lambda url, **kwargs: httpx.Response(200,
        request=httpx.Request("POST", url), json={"candidates": []}))

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

    stub_stream(monkeypatch, post)
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
    assert kwargs["timeout"] == 20.0


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
    stub_stream(monkeypatch, lambda *a, **k: response)
    assert GeminiAIProvider("test-key").generate_summary("document").output_text == "first second"


def test_gemini_rejects_truncated_text(monkeypatch):
    response = httpx.Response(200, request=httpx.Request("POST", "https://example.invalid"), json={
        "candidates": [{"finishReason": "MAX_TOKENS", "content": {"parts": [{"text": "partial"}]}}],
    })
    stub_stream(monkeypatch, lambda *a, **k: response)
    with pytest.raises(RuntimeError):
        GeminiAIProvider("test-key").generate_summary("document")


def test_gemini_failures_do_not_retain_secret_exception_context(monkeypatch, caplog):
    def fail(*a, **k):
        raise RuntimeError("test-key private document")
    stub_stream(monkeypatch, fail)
    with pytest.raises(RuntimeError) as error:
        GeminiAIProvider("test-key").generate_summary("private document")
    assert "test-key" not in str(error.value)
    assert error.value.__suppress_context__ is True
    assert "test-key" not in caplog.text and "private document" not in caplog.text
