from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import ApiResponse, SourceCapabilityRead
from app.api.errors import PublicApiError
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.services.source_capability import list_source_capabilities


router = APIRouter(prefix="/api/source-capabilities", tags=["source-capabilities"])


@router.get("", response_model=ApiResponse[list[SourceCapabilityRead]])
def get_source_capabilities(
    market: str | None = None,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ApiResponse[list[SourceCapabilityRead]]:
    try:
        capabilities = list_source_capabilities(db=db, settings=settings, market=market)
    except ValueError as exc:
        raise PublicApiError(
            status_code=400,
            code="UNSUPPORTED_MARKET",
            message="Unsupported market. Use US or IN.",
            field="market",
        ) from exc

    return ApiResponse(data=[SourceCapabilityRead.model_validate(item) for item in capabilities])
