from app.providers.base import BaseAIProvider, AIProviderResult

class MockAIProvider(BaseAIProvider):
    """A deterministic mocked AI provider for testing."""

    def generate_summary(self, text: str) -> AIProviderResult:
        return AIProviderResult(
            model_name="mock-model",
            output_text=(
                "**Mock Data: AI Summary**\n\n"
                "- The company reported strong performance but cited macroeconomic headwinds.\n"
                "- Key risks include supply chain disruptions and regulatory changes.\n"
                "- Forward guidance was adjusted downwards.\n"
                "\n*This deterministic output is for tests or explicitly enabled demo mode.*"
            ),
            limitations="This is a mocked response. It does not reflect the actual document content.",
            confidence_label="High (Deterministic)"
        )

    def generate_chat_response(self, messages: list[dict], context: str = "") -> AIProviderResult:
        return AIProviderResult(
            model_name="mock-model",
            output_text=(
                "**Claim:**\nThis is a mocked AI response.\n\n"
                "**Reasoning:**\nExplicit demo mode is enabled or automated tests are running.\n\n"
                "**Evidence:**\nThe backend is currently using the MockAIProvider.\n\n"
                "**Confidence:**\nHigh"
            ),
            limitations="This is a mocked response.",
            confidence_label="High (Deterministic)"
        )

    def generate_structured_response(self, prompt: str, schema: dict) -> AIProviderResult:
        import json

        properties = schema.get("properties", {})
        if "cluster_name" in properties:
            mock_data = {
                "cluster_name": "Mock Data: Narrative Cluster",
                "claim_text": "Mock Data: deterministic narrative claim.",
                "context_text": "Mock Data: no model-derived evidence.",
            }
        elif "impacts" in properties:
            mock_data = {"impacts": []}
        else:
            mock_data = {
                "target_operating_margin": 0.15,
                "target_operating_margin_reason": "Mocked AI reason: margins should expand slightly.",
                "revenue_growth_years": {"1": 0.1, "2": 0.1, "3": 0.08, "4": 0.08, "5": 0.05},
                "revenue_growth_reason": "Mocked AI reason: growth decelerates.",
                "sales_to_capital_ratio": 2.0,
                "sales_to_capital_reason": "Mocked AI reason: deterministic reinvestment efficiency.",
                "terminal_growth_rate": 0.02,
                "terminal_growth_reason": "Mocked AI reason: deterministic steady-state growth.",
            }

        return AIProviderResult(
            model_name="mock-model",
            output_text=json.dumps(mock_data),
            limitations="This is a mocked JSON response.",
            confidence_label="High (Deterministic)"
        )

    @property
    def provider_name(self) -> str:
        return "mock"
