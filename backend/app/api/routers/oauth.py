from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime

from app.db.session import get_db
from app.models.oauth_token import OAuthToken
from app.core.security import encrypt_token
from pydantic import BaseModel
from app.api.schemas import ApiResponse
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
def store_token(payload: TokenStoreRequest, db: Session = Depends(get_db)):
    """Stores an encrypted OAuth token in the database."""
    # Try to find existing token for provider
    existing_token = db.scalar(
        select(OAuthToken).where(OAuthToken.provider_name == payload.provider_name)
    )

    try:
        enc_access = encrypt_token(payload.access_token)
        enc_refresh = encrypt_token(payload.refresh_token) if payload.refresh_token else None
    except ValueError as exc:
        raise PublicApiError(
            status_code=503,
            code="TOKEN_ENCRYPTION_NOT_CONFIGURED",
            message="OAuth token encryption is not configured.",
        ) from exc

    if existing_token:
        existing_token.encrypted_access_token = enc_access
        existing_token.encrypted_refresh_token = enc_refresh
        existing_token.scopes = payload.scopes
        existing_token.expires_at = payload.expires_at
    else:
        new_token = OAuthToken(
            provider_name=payload.provider_name,
            encrypted_access_token=enc_access,
            encrypted_refresh_token=enc_refresh,
            scopes=payload.scopes,
            expires_at=payload.expires_at
        )
        db.add(new_token)

    db.commit()
    return ApiResponse(data={"status": "success", "message": f"Token securely stored for {payload.provider_name}"})

@router.get("/oauth/status", response_model=ApiResponse[list[TokenStatusResponse]])
def get_oauth_status(db: Session = Depends(get_db)):
    """Returns the connection status of all OAuth providers without exposing the tokens."""
    tokens = db.scalars(select(OAuthToken)).all()
    return ApiResponse(data=[
        TokenStatusResponse(
            provider_name=token.provider_name,
            is_connected=True,
            expires_at=token.expires_at
        )
        for token in tokens
    ])
