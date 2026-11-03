"""Default per-path request limits, independent of FastAPI's lazy route tree."""
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request

from app.api.errors import rate_limit_exception_handler


class RequestRateLimitMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            limiter = request.app.state.limiter
            try:
                # SlowAPI 0.1.9's middleware skips lazy included routers. Its
                # pinned limiter API supports URL-keyed default limits without
                # an endpoint. No route exemptions/decorators are used here.
                limiter._check_request_limit(request, None, in_middleware=True)
            except RateLimitExceeded as exc:
                response = await rate_limit_exception_handler(request, exc)
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)
