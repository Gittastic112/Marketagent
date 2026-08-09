from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.request_context import normalize_request_id, request_id_context
from app.api.errors import (
    http_exception_handler,
    rate_limit_exception_handler,
    request_validation_exception_handler,
    response_validation_exception_handler,
    unhandled_exception_handler,
)

from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

settings = get_settings()
configure_logging(settings.log_level)
app = FastAPI(title=settings.app_name)

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
app.add_exception_handler(ResponseValidationError, response_validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_request_context(request: Request, call_next):
    request_id = normalize_request_id(request.headers.get("X-Request-ID"))
    request.state.request_id = request_id
    token = request_id_context.set(request_id)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        request_id_context.reset(token)

app.include_router(router)

from app.api.schemas import ApiResponse

@app.get("/api/health", response_model=ApiResponse[dict[str, str]])
def health() -> ApiResponse[dict[str, str]]:
    return ApiResponse(data={"status": "ok", "app": settings.app_name})



@app.get("/health", response_model=ApiResponse[dict[str, str]])
def legacy_health() -> ApiResponse[dict[str, str]]:
    return ApiResponse(data={"status": "ok", "app": settings.app_name})
