from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
import logging
import os

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.hashing import sha256_text
from app.models.ai import AiOutput
from app.providers.ai_provider import DEFAULT_GEMINI_MODEL, GeminiAIProvider
from app.providers.base import AIProviderResult, BaseAIProvider
from app.providers.mock_provider import MockAIProvider
from app.services.ai_consent import ConsentPolicyError, authorize_external_call, disclosure_version


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
    expected = disclosure_version()
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
    valuation_basis: dict | None = None
    action_key: str | None = None
    privacy_disclosure_version: str | None = None


def require_provider_consent(db: Session, *, provider: BaseAIProvider, provenance: AIProvenance) -> int | None:
    # Exempt the actual local implementation, never a provider claiming the name "mock".
    if isinstance(provider, MockAIProvider):
        return None
    try:
        decision = authorize_external_call(db, user_id=provenance.user_id,
            provider_name=provider.provider_name, action_key=provenance.action_key,
            acknowledgement=provenance.privacy_disclosure_version, data_classes=provenance.external_data_classes)
    except ConsentPolicyError as exc:
        raise AIExecutionError(code=exc.code, message=exc.message, status_code=exc.status_code,
            retryable=False, provider_name=provider.provider_name) from exc
    return decision.id


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
    consent_decision_id: int | None = None,
    execution_metadata: dict | None = None,
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
        privacy_disclosure_version=provenance.privacy_disclosure_version or disclosure_version(),
        consent_decision_id=consent_decision_id,
        external_data_classes_json=list(provenance.external_data_classes),
        transmission_scope=transmission_scope or ("none" if is_mock else "external_provider"),
        execution_status=execution_status,
        failure_code=failure_code,
        output_text=output_text,
        limitations=limitations,
        confidence_label=confidence_label,
        human_review_status="pending",
        evaluation_json={
            **({"valuation_basis": provenance.valuation_basis} if provenance.valuation_basis else {}),
            **({"execution": execution_metadata} if execution_metadata else {}),
        } or None,
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
        consent_decision_id = require_provider_consent(db, provider=selected_provider, provenance=provenance)
    except AIExecutionError as exc:
        persist_ai_output(db, provenance=provenance, provider_name=selected_provider.provider_name,
            model_name="not_requested", is_mock=False, output_text="", limitations=exc.message,
            confidence_label="none", execution_status="failed", failure_code=exc.code,
            transmission_scope="none")
        raise

    previous = db.scalar(select(AiOutput.id).where(
        AiOutput.user_id == provenance.user_id,
        AiOutput.reference_type == provenance.reference_type,
        AiOutput.reference_id == provenance.reference_id,
        AiOutput.prompt_version == provenance.prompt_version,
        AiOutput.input_hash == sha256_text(provenance.input_text),
        AiOutput.execution_status.in_(("pending", "failed", "unknown")),
    ).order_by(AiOutput.id.desc()).limit(1))
    is_mock = isinstance(selected_provider, MockAIProvider)
    attempt = persist_ai_output(db, provenance=provenance,
        provider_name=selected_provider.provider_name,
        model_name=getattr(selected_provider, "model_name", "not_confirmed"),
        is_mock=is_mock, output_text="", confidence_label="none",
        limitations="Attempt recorded. Completion and remote delivery are not confirmed. Check its result before explicitly retrying.",
        execution_status="pending", transmission_scope="none" if is_mock else "unknown",
        consent_decision_id=consent_decision_id,
        execution_metadata={"previous_attempt_id": previous, "dispatch_recorded": True})
    attempt_id = attempt.id
    try:
        # The receipt is durable before dispatch; recheck permission at the send boundary.
        current_consent = require_provider_consent(db, provider=selected_provider, provenance=provenance)
        if current_consent != consent_decision_id:
            raise AIExecutionError(code="AI_CONSENT_CHANGED",
                message="AI permission changed before dispatch. Review permissions before retrying.",
                status_code=409, retryable=False, provider_name=selected_provider.provider_name)
    except AIExecutionError as exc:
        attempt.execution_status = "failed"
        attempt.failure_code = exc.code
        attempt.limitations = exc.message
        attempt.transmission_scope = "none"
        attempt.evaluation_json = {**(attempt.evaluation_json or {}), "execution": {
            **(attempt.evaluation_json or {}).get("execution", {}), "finished_at": datetime.now(UTC).isoformat()}}
        db.commit()
        raise

    try:
        result = generate(selected_provider)
    except Exception as exc:
        db.rollback()
        attempt = db.get(AiOutput, attempt_id)
        logger.error("AI provider execution failed", extra={
            "provider": selected_provider.provider_name, "exception_type": type(exc).__name__})
        error = AIProviderFailed(selected_provider.provider_name)
        attempt.execution_status = "failed"
        attempt.failure_code = error.code
        attempt.limitations = error.message + " Remote delivery may have occurred; no automatic retry was made."
        attempt.transmission_scope = "none" if is_mock else "unknown"
        attempt.evaluation_json = {**(attempt.evaluation_json or {}), "execution": {
            **(attempt.evaluation_json or {}).get("execution", {}), "finished_at": datetime.now(UTC).isoformat()}}
        db.commit()
        raise error from exc

    attempt.model_name = result.model_name
    attempt.output_text = result.output_text
    attempt.limitations = result.limitations
    attempt.confidence_label = result.confidence_label
    attempt.execution_status = "success"
    attempt.transmission_scope = "none" if is_mock else "external_provider"
    attempt.evaluation_json = {**(attempt.evaluation_json or {}), "execution": {
        **(attempt.evaluation_json or {}).get("execution", {}), "finished_at": datetime.now(UTC).isoformat()}}
    db.commit()
    db.refresh(attempt)
    return attempt
