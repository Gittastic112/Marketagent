from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.schemas import ApiResponse, ProviderHealthRead
from app.db.session import get_db
from app.services.provider_health import get_provider_health


router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.get("/health", response_model=ApiResponse[list[ProviderHealthRead]])
def list_provider_health(db: Session = Depends(get_db)) -> ApiResponse[list[ProviderHealthRead]]:
    return ApiResponse(data=get_provider_health(db))
