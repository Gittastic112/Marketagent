from app.providers.base import BaseAIProvider, AIProviderResult

class MockAIProvider(BaseAIProvider):
    """A deterministic mocked AI provider for testing."""
    
    def generate_summary(self, text: str) -> AIProviderResult:
        return AIProviderResult(
            model_name="mock-model",
            output_text=(
                "**Mocked AI Summary**\n\n"
                "- The company reported strong performance but cited macroeconomic headwinds.\n"
                "- Key risks include supply chain disruptions and regulatory changes.\n"
                "- Forward guidance was adjusted downwards.\n"
                "\n*Note: This is a mocked response because no API key was provided or tests are running.*"
            ),
            limitations="This is a mocked response. It does not reflect the actual document content.",
            confidence_label="High (Deterministic)"
        )

    def generate_chat_response(self, messages: list[dict], context: str = "") -> AIProviderResult:
        return AIProviderResult(
            model_name="mock-model",
            output_text=(
                "**Claim:**\nThis is a mocked AI response.\n\n"
                "**Reasoning:**\nNo API key was provided or tests are running.\n\n"
                "**Evidence:**\nThe backend is currently using the MockAIProvider.\n\n"
                "**Confidence:**\nHigh"
            ),
            limitations="This is a mocked response.",
            confidence_label="High (Deterministic)"
        )

    @property
    def provider_name(self) -> str:
        return "mock"
