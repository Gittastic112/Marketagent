from collections.abc import Callable
from dataclasses import dataclass
import logging
import os

from sqlalchemy.orm import Session

from app.core.hashing import sha256_text
from app.models.ai import AiOutput
from app.providers.ai_provider import DEFAULT_GEMINI_MODEL, GeminiAIProvider
from app.providers.base import AIProviderResult, BaseAIProvider
from app.providers.mock_provider import MockAIProvider


logger = logging.getLogger(__name__)
DEFAULT_PRIVACY_DISCLOSURE_VERSION = "v1"


class AIExecutionError(RuntimeError):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int,
        retryable: bool,
        provider_name: str,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.retryable = retryable
        self.provider_name = provider_name


class AIProviderNotConfigured(AIExecutionError):
    def __init__(self) -> None:
        super().__init__(
            code="AI_PROVIDER_NOT_CONFIGURED",
            message="AI is not configured. Add GEMINI_API_KEY or explicitly enable AI_DEMO_MODE.",
            status_code=503,
            retryable=False,
            provider_name="unconfigured",
        )


class AIProviderFailed(AIExecutionError):
    def __init__(self, provider_name: str) -> None:
        super().__init__(
            code="AI_PROVIDER_FAILED",
            message="The AI provider could not complete the request.",
            status_code=502,
            retryable=True,
            provider_name=provider_name,
        )


class AIPrivacyDisclosureRequired(AIExecutionError):
    def __init__(self) -> None:
        super().__init__(
            code="AI_PRIVACY_DISCLOSURE_REQUIRED",
            message="Review and acknowledge the current AI data disclosure before continuing.",
            status_code=409,
            retryable=False,
            provider_name="none",
        )


def _is_enabled(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def select_ai_provider() -> BaseAIProvider:
    if os.environ.get("PYTEST_CURRENT_TEST") is not None:
        return MockAIProvider()
    if _is_enabled(os.environ.get("AI_DEMO_MODE")):
        return MockAIProvider()
    api_key = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if api_key:
        return GeminiAIProvider(api_key=api_key, model_name=os.environ.get("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL)
    raise AIProviderNotConfigured()


def require_privacy_disclosure(version: str | None) -> None:
    expected = os.environ.get(
        "AI_PRIVACY_DISCLOSURE_VERSION",
        DEFAULT_PRIVACY_DISCLOSURE_VERSION,
    )
    if version != expected:
        raise AIPrivacyDisclosureRequired()


@dataclass(frozen=True)
class AIProvenance:
    user_id: str
    prompt_version: str
    input_text: str
    reference_type: str | None = None
    reference_id: int | None = None
    raw_document_id: int | None = None
    source_ids: tuple[str, ...] = ()
    source_scope: str = "unspecified"
    external_data_classes: tuple[str, ...] = ()


def persist_ai_output(
    db: Session,
    *,
    provenance: AIProvenance,
    provider_name: str,
    model_name: str,
    is_mock: bool,
    output_text: str,
    limitations: str | None,
    confidence_label: str,
    execution_status: str = "success",
    failure_code: str | None = None,
    transmission_scope: str | None = None,
) -> AiOutput:
    output = AiOutput(
        user_id=provenance.user_id,
        raw_document_id=provenance.raw_document_id,
        reference_type=provenance.reference_type,
        reference_id=provenance.reference_id,
        model_name=model_name,
        provider_name=provider_name,
        is_mock=is_mock,
        prompt_version=provenance.prompt_version,
        input_hash=sha256_text(provenance.input_text),
        source_ids_json=list(provenance.source_ids),
        source_scope=provenance.source_scope,
        privacy_disclosure_version=os.environ.get(
            "AI_PRIVACY_DISCLOSURE_VERSION",
            DEFAULT_PRIVACY_DISCLOSURE_VERSION,
        ),
        external_data_classes_json=list(provenance.external_data_classes),
        transmission_scope=transmission_scope or ("none" if is_mock else "external_provider"),
        execution_status=execution_status,
        failure_code=failure_code,
        output_text=output_text,
        limitations=limitations,
        confidence_label=confidence_label,
        human_review_status="pending",
    )
    db.add(output)
    db.commit()
    db.refresh(output)
    return output


def execute_ai_generation(
    db: Session,
    *,
    provenance: AIProvenance,
    generate: Callable[[BaseAIProvider], AIProviderResult],
    provider: BaseAIProvider | None = None,
) -> AiOutput:
    try:
        selected_provider = provider or select_ai_provider()
    except AIProviderNotConfigured as exc:
        persist_ai_output(
            db,
            provenance=provenance,
            provider_name=exc.provider_name,
            model_name="unavailable",
            is_mock=False,
            output_text="",
            limitations=exc.message,
            confidence_label="none",
            execution_status="failed",
            failure_code=exc.code,
            transmission_scope="none",
        )
        raise

    try:
        result = generate(selected_provider)
    except Exception as exc:
        provider_name = selected_provider.provider_name
        is_mock = provider_name == "mock"
        logger.error(
            "AI provider execution failed",
            extra={"provider": provider_name, "exception_type": type(exc).__name__},
        )
        error = AIProviderFailed(provider_name)
        persist_ai_output(
            db,
            provenance=provenance,
            provider_name=provider_name,
            model_name="unavailable",
            is_mock=is_mock,
            output_text="",
            limitations=error.message,
            confidence_label="none",
            execution_status="failed",
            failure_code=error.code,
            transmission_scope="none" if is_mock else "external_provider",
        )
        raise error from exc

    is_mock = selected_provider.provider_name == "mock"
    return persist_ai_output(
        db,
        provenance=provenance,
        provider_name=selected_provider.provider_name,
        model_name=result.model_name,
        is_mock=is_mock,
        output_text=result.output_text,
        limitations=result.limitations,
        confidence_label=result.confidence_label,
    )
