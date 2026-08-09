from app.api.errors import PublicApiError
from app.api.schemas import ApiMeta
from app.models.ai import AiOutput
from app.services.ai_contract import AIExecutionError


def public_ai_error(exc: AIExecutionError) -> PublicApiError:
    return PublicApiError(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        retryable=exc.retryable,
        provider=exc.provider_name,
    )


def ai_output_meta(output: AiOutput) -> ApiMeta:
    warnings = ["Mock Data"] if output.is_mock else []
    if output.execution_status == "failed" and output.failure_code:
        warnings.append(output.failure_code)
    return ApiMeta(
        source=output.provider_name,
        is_mock=output.is_mock,
        warnings=warnings,
        confidence=output.confidence_label,
    )
