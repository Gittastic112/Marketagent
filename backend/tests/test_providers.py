import pytest
from app.providers.mock_provider import MockAIProvider
from app.providers.ai_provider import GeminiAIProvider

def test_mock_provider():
    provider = MockAIProvider()
    result = provider.generate_summary("test text")
    
    assert provider.provider_name == "mock"
    assert result.model_name == "mock-model"
    assert "Mocked AI Summary" in result.output_text
    assert result.confidence_label == "High (Deterministic)"

def test_gemini_provider_init():
    provider = GeminiAIProvider(api_key="test-key")
    assert provider.provider_name == "gemini"
    assert provider.api_key == "test-key"
