import logging
from http import HTTPStatus
from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.responses import JSONResponse

from app.api.schemas import ApiErrorDetail, ApiMeta, ApiResponse


logger = logging.getLogger(__name__)


STATUS_CODES = {
    400: "INVALID_REQUEST",
    401: "NOT_AUTHENTICATED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    413: "FILE_TOO_LARGE",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
    502: "PROVIDER_UNAVAILABLE",
    503: "SERVICE_UNAVAILABLE",
}


class PublicApiError(HTTPException):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        retryable: bool = False,
        field: str | None = None,
        provider: str | None = None,
        processing_run_id: int | None = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.field = field
        self.provider = provider
        self.processing_run_id = processing_run_id


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return str(value)


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _error_response(
    request: Request,
    *,
    status_code: int,
    errors: list[ApiErrorDetail],
    legacy_detail: Any,
) -> JSONResponse:
    response = ApiResponse[Any](
        data=None,
        meta=ApiMeta(status="error", request_id=_request_id(request)),
        errors=errors,
    ).model_dump(mode="json")
    # Transitional compatibility for callers that still read FastAPI's detail field.
    response["detail"] = _json_safe(legacy_detail)
    return JSONResponse(status_code=status_code, content=response)


def _http_message(status_code: int, detail: Any) -> str:
    if status_code >= 500:
        return "The request could not be completed."
    if isinstance(detail, str) and detail.strip():
        return detail
    if isinstance(detail, dict) and isinstance(detail.get("message"), str):
        return detail["message"]
    try:
        return HTTPStatus(status_code).phrase
    except ValueError:
        return "Request failed"


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc, PublicApiError):
        error = ApiErrorDetail(
            code=exc.code,
            message=exc.message,
            retryable=exc.retryable,
            field=exc.field,
            provider=exc.provider,
            processing_run_id=exc.processing_run_id,
        )
        return _error_response(
            request,
            status_code=exc.status_code,
            errors=[error],
            legacy_detail=exc.message,
        )

    message = _http_message(exc.status_code, exc.detail)
    error = ApiErrorDetail(
        code=STATUS_CODES.get(exc.status_code, "REQUEST_FAILED"),
        message=message,
        retryable=exc.status_code in {429, 502, 503, 504},
    )
    return _error_response(
        request,
        status_code=exc.status_code,
        errors=[error],
        legacy_detail=message,
    )


async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    errors = []
    for issue in exc.errors():
        location = issue.get("loc", ())
        field = str(location[-1]) if location else None
        errors.append(
            ApiErrorDetail(
                code="VALIDATION_ERROR",
                message=issue.get("msg", "Invalid value"),
                target=".".join(str(part) for part in location) or None,
                field=field,
            )
        )
    return _error_response(
        request,
        status_code=422,
        errors=errors,
        legacy_detail=exc.errors(),
    )


async def response_validation_exception_handler(
    request: Request,
    exc: ResponseValidationError,
) -> JSONResponse:
    logger.error(
        "Response validation failed",
        extra={"path": request.url.path, "error_code": "RESPONSE_VALIDATION_ERROR"},
    )
    message = "The server returned an invalid response."
    return _error_response(
        request,
        status_code=500,
        errors=[ApiErrorDetail(code="INTERNAL_RESPONSE_ERROR", message=message)],
        legacy_detail=message,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled request failure",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error_code": "INTERNAL_ERROR",
            "exception_type": type(exc).__name__,
        },
    )
    message = "The request could not be completed."
    return _error_response(
        request,
        status_code=500,
        errors=[ApiErrorDetail(code="INTERNAL_ERROR", message=message)],
        legacy_detail=message,
    )


async def rate_limit_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    message = "Too many requests. Retry later."
    return _error_response(
        request,
        status_code=429,
        errors=[ApiErrorDetail(code="RATE_LIMITED", message=message, retryable=True)],
        legacy_detail=message,
    )
