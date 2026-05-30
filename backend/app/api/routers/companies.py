from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.helpers import commit_or_conflict, company_has_linked_records, create_record, delete_record, get_or_404, update_record
from app.api.schemas import ApiResponse, CompanyCreate, CompanyLookupRead, CompanyRead, CompanyUpdate, SecFilingMetadataCreate
from app.db.session import get_db
from app.models import Company
from app.services.sec_ingestion import (
    SecFilingMetadata,
    fetch_recent_sec_filing_metadata,
    lookup_cik_for_ticker,
    lookup_company_profile_for_ticker,
)


router = APIRouter()


@router.post("/companies", response_model=ApiResponse[CompanyRead], status_code=status.HTTP_201_CREATED)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)) -> Company:
    existing = db.scalar(select(Company).where(Company.ticker == payload.ticker.upper()))
    if existing is not None:
        raise HTTPException(status_code=409, detail=f"Company ticker {payload.ticker.upper()} already exists")
    return ApiResponse(data=create_record(db, Company, payload))


@router.get("/companies", response_model=ApiResponse[list[CompanyRead]])
def list_companies(db: Session = Depends(get_db)) -> list[Company]:
    return ApiResponse(data=list(db.scalars(select(Company).order_by(Company.id))))


@router.get("/companies/lookup", response_model=ApiResponse[CompanyLookupRead])
def lookup_company_by_ticker(ticker: str) -> ApiResponse[dict[str, str]]:
    try:
        profile = lookup_company_profile_for_ticker(ticker)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"SEC company lookup failed: {exc}") from exc
    if profile is None:
        raise HTTPException(status_code=404, detail="Company ticker not found in SEC company tickers")
    return ApiResponse(data={"ticker": profile.ticker, "name": profile.title, "cik": profile.cik})


@router.get("/sec/company/{ticker}/cik")
def get_sec_company_cik(ticker: str) -> ApiResponse[dict[str, str]]:
    try:
        profile = lookup_company_profile_for_ticker(ticker)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"SEC company lookup failed: {exc}") from exc
    if profile is None:
        raise HTTPException(status_code=404, detail="Company ticker not found in SEC company tickers")
    return ApiResponse(data={"ticker": profile.ticker, "cik": profile.cik})


@router.get("/companies/{company_id}", response_model=ApiResponse[CompanyRead])
def get_company(company_id: int, db: Session = Depends(get_db)) -> Company:
    return ApiResponse(data=get_or_404(db, Company, company_id))


@router.patch("/companies/{company_id}", response_model=ApiResponse[CompanyRead])
def update_company(company_id: int, payload: CompanyUpdate, db: Session = Depends(get_db)) -> Company:
    return ApiResponse(data=update_record(db, get_or_404(db, Company, company_id), payload))


@router.delete("/companies/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(company_id: int, db: Session = Depends(get_db)) -> None:
    company = get_or_404(db, Company, company_id)
    if company_has_linked_records(db, company_id):
        raise HTTPException(
            status_code=409,
            detail=(
                "Company cannot be deleted while it has linked records. "
                "Delete linked documents, events, alerts, and thesis notes first, or mark the company inactive."
            ),
        )
    delete_record(db, company)


@router.post("/companies/{company_id}/lookup-cik", response_model=ApiResponse[CompanyRead])
def lookup_company_cik(company_id: int, db: Session = Depends(get_db)) -> Company:
    company = get_or_404(db, Company, company_id)
    try:
        cik = lookup_cik_for_ticker(company.ticker)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"SEC CIK lookup failed: {exc}") from exc
    if cik is None:
        raise HTTPException(status_code=404, detail="CIK not found")
    company.cik = cik
    commit_or_conflict(db)
    db.refresh(company)
    return ApiResponse(data=company)


@router.get("/companies/{company_id}/sec-filings/preview", response_model=ApiResponse[list[SecFilingMetadataCreate]])
def preview_company_sec_filings(
    company_id: int,
    form_type: str = "10-K",
    filing_year: int | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
) -> list[SecFilingMetadata]:
    company = get_or_404(db, Company, company_id)
    if not company.cik:
        raise HTTPException(status_code=409, detail="Company needs a CIK before SEC filing preview")
    try:
        return ApiResponse(data=fetch_recent_sec_filing_metadata(
            company.cik,
            form_types=(form_type,),
            filing_year=filing_year,
            limit=limit,
        ))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"SEC filing preview failed: {exc}") from exc

@router.post("/companies/{company_id}/exposure-tags", response_model=ApiResponse[CompanyRead])
def add_exposure_tag(company_id: int, payload: dict, db: Session = Depends(get_db)) -> Company:
    company = get_or_404(db, Company, company_id)
    tag_id = payload.get("tag_id")
    if not tag_id:
        raise HTTPException(status_code=400, detail="tag_id is required")
        
    from app.models.company import ExposureTag
    tag = db.get(ExposureTag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Exposure tag not found")
        
    if tag not in company.exposure_tags:
        company.exposure_tags.append(tag)
        db.commit()
        db.refresh(company)
        
    return ApiResponse(data=company)

@router.delete("/companies/{company_id}/exposure-tags/{tag_id}", response_model=ApiResponse[CompanyRead])
def remove_exposure_tag(company_id: int, tag_id: int, db: Session = Depends(get_db)) -> Company:
    company = get_or_404(db, Company, company_id)
    
    from app.models.company import ExposureTag
    tag = db.get(ExposureTag, tag_id)
    if tag and tag in company.exposure_tags:
        company.exposure_tags.remove(tag)
        db.commit()
        db.refresh(company)
        
    return ApiResponse(data=company)

from fastapi.responses import Response

@router.get("/companies/{company_id}/memo")
def export_company_memo(company_id: int, db: Session = Depends(get_db)):
    company = get_or_404(db, Company, company_id)
    
    # Gather thesis notes
    from app.models.thesis import ThesisNote
    notes = db.scalars(select(ThesisNote).where(ThesisNote.company_id == company_id).order_by(ThesisNote.created_at.desc())).all()
    
    # Gather recent events
    from app.models.event import Event
    events = db.scalars(select(Event).where(Event.company_id == company_id).order_by(Event.event_date.desc()).limit(10)).all()
    
    lines = []
    lines.append(f"# Investment Memo: {company.name} ({company.ticker})")
    lines.append("")
    lines.append(f"**Sector:** {company.sector or '-'} | **Industry:** {company.industry or '-'}")
    lines.append(f"**Exchange:** {company.exchange or '-'} | **Currency:** {company.currency or 'USD'}")
    lines.append("")
    
    if company.exposure_tags:
        tags = ", ".join(t.name for t in company.exposure_tags)
        lines.append(f"**Exposure Tags:** {tags}")
        lines.append("")
        
    lines.append("## Thesis Notes")
    if not notes:
        lines.append("No thesis notes recorded.")
    for note in notes:
        lines.append(f"### Note ({note.created_at.strftime('%Y-%m-%d')})")
        lines.append(note.content)
        lines.append("")
        
    lines.append("## Recent Events")
    if not events:
        lines.append("No recent events recorded.")
    for event in events:
        date_str = event.event_date.strftime('%Y-%m-%d') if event.event_date else "Unknown Date"
        lines.append(f"### {date_str} - {event.headline}")
        if event.summary:
            lines.append(event.summary)
        lines.append("")
        
    markdown_content = "\n".join(lines)
    
    response = Response(content=markdown_content, media_type="text/markdown")
    response.headers["Content-Disposition"] = f"attachment; filename=memo_{company.ticker}.md"
    return ApiResponse(data=response)
