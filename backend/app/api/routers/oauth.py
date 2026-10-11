from fastapi import APIRouter
from datetime import datetime

from pydantic import BaseModel
from app.schemas.common import ApiResponse
from app.api.errors import PublicApiError

router = APIRouter()

class TokenStoreRequest(BaseModel):
    provider_name: str
    access_token: str
    refresh_token: str | None = None
    scopes: str | None = None
    expires_at: datetime | None = None

class TokenStatusResponse(BaseModel):
    provider_name: str
    is_connected: bool
    expires_at: datetime | None = None

@router.post(
    "/oauth/store-token",
    response_model=ApiResponse[dict[str, str]],
    status_code=200,
)
def store_token(payload: TokenStoreRequest):
    """Legacy shape retained; no supported OAuth flow or owner-scoped vault yet."""
    raise PublicApiError(status_code=503, code="OAUTH_STORAGE_DISABLED",
        message="Token storage is disabled until an approved owner-scoped OAuth integration is implemented.")

@router.get("/oauth/status", response_model=ApiResponse[list[TokenStatusResponse]])
def get_oauth_status():
    """Retain any legacy encrypted rows without exposing a global token inventory."""
    return ApiResponse(data=[], meta={"status": "not_configured", "warnings": [
        "OAuth integrations and token storage are not available yet."]})
