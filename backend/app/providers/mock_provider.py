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

    @property
    def provider_name(self) -> str:
        return "mock"
