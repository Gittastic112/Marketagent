from datetime import date, datetime
from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.helpers import get_or_404
from app.api.schemas import ApiResponse, SourceFactRevisionRead
from app.db.session import get_db
from app.models import Company
from app.services.source_fact_history import list_source_facts_as_of
from app.schemas.dated_inputs import DatedInputsRead
from app.services.dated_financial_inputs import dated_financial_inputs


router = APIRouter()


@router.get("/companies/{company_id}/dated-inputs", response_model=ApiResponse[DatedInputsRead])
def get_dated_inputs(company_id: int, valuation_date: date,
    knowledge: Literal["available_by_date", "latest_recorded"] = "available_by_date",
    track: Literal["operating", "bank_equity", "equity_cash_flow"] = "operating",
    db: Session = Depends(get_db)):
    get_or_404(db, Company, company_id)
    return ApiResponse(data=dated_financial_inputs(db, company_id, valuation_date=valuation_date,
        knowledge=knowledge, track=track))


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
