from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.schemas import ApiResponse, FilingDiscoveryRead, RawDocumentRead
from app.db.session import get_db
from app.providers.filings import ManualFilingCreate
from app.services.filing_acquisition import (
    create_manual_company_filing_link,
    discover_company_filings,
    get_filing_document,
    list_company_filings,
)


router = APIRouter(prefix="/api", tags=["filing_acquisition"])


@router.get("/companies/{company_id}/filings/discover", response_model=ApiResponse[FilingDiscoveryRead])
def discover_filings(
    company_id: int,
    form_type: str | None = "10-K",
    filing_year: int | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
) -> ApiResponse[FilingDiscoveryRead]:
    discovery = discover_company_filings(
        db=db,
        company_id=company_id,
        form_type=form_type,
        filing_year=filing_year,
        limit=limit,
    )
    return ApiResponse(data=discovery, meta={"source": discovery.provider_name})


@router.post(
    "/companies/{company_id}/filings/manual-link",
    response_model=ApiResponse[RawDocumentRead],
    status_code=status.HTTP_201_CREATED,
)
def add_manual_filing_link(
    company_id: int,
    payload: ManualFilingCreate,
    db: Session = Depends(get_db),
) -> ApiResponse[RawDocumentRead]:
    return ApiResponse(data=create_manual_company_filing_link(db, company_id, payload))


@router.get("/companies/{company_id}/filings", response_model=ApiResponse[list[RawDocumentRead]])
def get_company_filings(company_id: int, db: Session = Depends(get_db)) -> ApiResponse[list[RawDocumentRead]]:
    return ApiResponse(data=list_company_filings(db, company_id))


@router.get("/filings/{filing_id}", response_model=ApiResponse[RawDocumentRead])
def get_filing(filing_id: int, db: Session = Depends(get_db)) -> ApiResponse[RawDocumentRead]:
    return ApiResponse(data=get_filing_document(db, filing_id))
