from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.helpers import get_or_404
from app.api.schemas import ApiResponse, SourceFactRevisionRead
from app.db.session import get_db
from app.models import Company
from app.services.source_fact_history import list_source_facts_as_of


router = APIRouter()


@router.get(
    "/companies/{company_id}/source-facts",
    response_model=ApiResponse[list[SourceFactRevisionRead]],
)
def get_company_source_facts(
    company_id: int,
    as_of: datetime | None = None,
    db: Session = Depends(get_db),
) -> ApiResponse[list]:
    get_or_404(db, Company, company_id)
    return ApiResponse(data=list_source_facts_as_of(db, company_id, as_of=as_of))
