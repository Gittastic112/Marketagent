import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.helpers import commit_or_conflict, company_has_linked_records, create_record, delete_record, get_or_404, update_record
from app.api.errors import PublicApiError
from app.api.schemas import (
    ApiResponse,
    CompanyCreate,
    CompanyLookupRead,
    CompanyRead,
    CompanyIndustryMixRead,
    CompanyIndustryMixUpdate,
    CompanyUpdate,
    RawDocumentRead,
    SecFilingMetadataCreate,
)
from app.db.session import get_db
from app.models import Company
from app.services.sec_ingestion import (
    SecFilingMetadata,
    fetch_recent_sec_filing_metadata,
    lookup_cik_for_ticker,
)
from app.services.company_lookup import lookup_company
from app.providers.filings import ManualFilingCreate, get_filing_provider
from app.services.filing_manual import create_manual_filing


router = APIRouter()
logger = logging.getLogger(__name__)

SUPPORTED_MARKETS = {
    "US": {"country": "United States", "currency": "USD"},
    "IN": {"country": "India", "currency": "INR"},
}


def _normalized_upper(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped.upper() if stripped else None


def _normalize_market(value: str | None) -> str:
    market = _normalized_upper(value) or "US"
    if market not in SUPPORTED_MARKETS:
        raise HTTPException(status_code=400, detail=f"Unsupported market {market}")
    return market


def _normalize_company_create(payload: CompanyCreate) -> CompanyCreate:
    payload.ticker = _normalized_upper(payload.ticker) or payload.ticker
    payload.market = _normalize_market(payload.market)
    payload.primary_exchange = _normalized_upper(payload.primary_exchange or payload.exchange)
    payload.local_symbol = _normalized_upper(payload.local_symbol or payload.ticker)
    payload.exchange = _normalized_upper(payload.exchange or payload.primary_exchange)
    payload.currency = _normalized_upper(payload.currency) or SUPPORTED_MARKETS[payload.market]["currency"]
    payload.country = payload.country or SUPPORTED_MARKETS[payload.market]["country"]
    payload.isin = _normalized_upper(payload.isin)
    payload.figi = _normalized_upper(payload.figi)
    payload.regulatory_id = _normalized_upper(payload.regulatory_id or payload.cik)
    payload.regulatory_id_type = _normalized_upper(payload.regulatory_id_type)
    return payload


def _normalize_company_update(payload: CompanyUpdate, company: Company) -> CompanyUpdate:
    changes = payload.model_dump(exclude_unset=True)
    if "ticker" in changes:
        payload.ticker = _normalized_upper(payload.ticker)
        if "local_symbol" not in changes and payload.ticker:
            payload.local_symbol = payload.ticker

    if "market" in changes:
        payload.market = _normalize_market(payload.market)
        if "currency" not in changes and not company.currency:
            payload.currency = SUPPORTED_MARKETS[payload.market]["currency"]
        if "country" not in changes and not company.country:
            payload.country = SUPPORTED_MARKETS[payload.market]["country"]

    if "primary_exchange" in changes:
        payload.primary_exchange = _normalized_upper(payload.primary_exchange)
        if "exchange" not in changes:
            payload.exchange = payload.primary_exchange
    elif "exchange" in changes:
        payload.exchange = _normalized_upper(payload.exchange)
        payload.primary_exchange = payload.exchange

    if "local_symbol" in changes:
        payload.local_symbol = _normalized_upper(payload.local_symbol)
    if "exchange" in changes:
        payload.exchange = _normalized_upper(payload.exchange)
    if "currency" in changes:
        payload.currency = _normalized_upper(payload.currency)
    if "isin" in changes:
        payload.isin = _normalized_upper(payload.isin)
    if "figi" in changes:
        payload.figi = _normalized_upper(payload.figi)
    if "regulatory_id" in changes:
        payload.regulatory_id = _normalized_upper(payload.regulatory_id)
    if "regulatory_id_type" in changes:
        payload.regulatory_id_type = _normalized_upper(payload.regulatory_id_type)

    return payload


def _find_existing_market_identity(db: Session, market: str, primary_exchange: str | None, local_symbol: str | None) -> Company | None:
    return db.scalar(
        select(Company).where(
            Company.market == market,
            Company.primary_exchange == primary_exchange,
            Company.local_symbol == local_symbol,
        )
    )


@router.post("/companies", response_model=ApiResponse[CompanyRead], status_code=status.HTTP_201_CREATED)
def create_company(payload: CompanyCreate, db: Session = Depends(get_db)) -> Company:
    payload = _normalize_company_create(payload)
    existing = _find_existing_market_identity(db, payload.market, payload.primary_exchange, payload.local_symbol)
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Company identity {payload.market}/{payload.primary_exchange or '-'}"
            f"/{payload.local_symbol or payload.ticker} already exists",
        )
    return ApiResponse(data=create_record(db, Company, payload))


@router.get("/companies", response_model=ApiResponse[list[CompanyRead]])
def list_companies(db: Session = Depends(get_db)) -> list[Company]:
    return ApiResponse(data=list(db.scalars(select(Company).order_by(Company.id))))


@router.get("/companies/lookup", response_model=ApiResponse[CompanyLookupRead])
def lookup_company_by_ticker(
    ticker: str,
    market: str | None = None,
    exchange: str | None = None,
    db: Session = Depends(get_db),
) -> ApiResponse[CompanyLookupRead]:
    try:
        result = lookup_company(db=db, ticker=ticker, market=market, exchange=exchange)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Company lookup provider failed",
            extra={"provider": "company_lookup", "exception_type": type(exc).__name__},
        )
        raise PublicApiError(
            status_code=502,
            code="COMPANY_LOOKUP_FAILED",
            message="Company lookup is temporarily unavailable.",
            retryable=True,
            provider="company_lookup",
        ) from exc
    return ApiResponse(data=CompanyLookupRead(**result.model_dump()))


@router.get("/sec/company/{ticker}/cik")
def get_sec_company_cik(ticker: str) -> ApiResponse[dict[str, str]]:
    try:
        result = lookup_cik_for_ticker(ticker)
    except Exception as exc:
        logger.error(
            "SEC company lookup failed",
            extra={"provider": "SEC EDGAR", "exception_type": type(exc).__name__},
        )
        raise PublicApiError(
            status_code=502,
            code="SEC_COMPANY_LOOKUP_FAILED",
            message="SEC company lookup is temporarily unavailable.",
            retryable=True,
            provider="SEC EDGAR",
        ) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="Company ticker not found in SEC company tickers")
    return ApiResponse(data={"ticker": ticker.upper(), "cik": result})


@router.get("/companies/{company_id}", response_model=ApiResponse[CompanyRead])
def get_company(company_id: int, db: Session = Depends(get_db)) -> Company:
    return ApiResponse(data=get_or_404(db, Company, company_id))


@router.patch("/companies/{company_id}", response_model=ApiResponse[CompanyRead])
def update_company(company_id: int, payload: CompanyUpdate, db: Session = Depends(get_db)) -> Company:
    company = get_or_404(db, Company, company_id)
    payload = _normalize_company_update(payload, company)

    market = payload.market if payload.market is not None else company.market
    primary_exchange = payload.primary_exchange if payload.primary_exchange is not None else company.primary_exchange
    local_symbol = payload.local_symbol if payload.local_symbol is not None else company.local_symbol
    existing = _find_existing_market_identity(db, market, primary_exchange, local_symbol)
    if existing is not None and existing.id != company.id:
        raise HTTPException(
            status_code=409,
            detail=f"Company identity {market}/{primary_exchange or '-'}/{local_symbol or company.ticker} already exists",
        )

    return ApiResponse(data=update_record(db, company, payload))


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
        logger.error(
            "SEC CIK lookup failed",
            extra={"provider": "SEC EDGAR", "exception_type": type(exc).__name__},
        )
        raise PublicApiError(
            status_code=502,
            code="SEC_CIK_LOOKUP_FAILED",
            message="SEC CIK lookup is temporarily unavailable.",
            retryable=True,
            provider="SEC EDGAR",
        ) from exc
    if cik is None:
        raise HTTPException(status_code=404, detail="CIK not found")
    company.cik = cik
    commit_or_conflict(db)
    db.refresh(company)
    return ApiResponse(data=company)


@router.get("/companies/{company_id}/filings/preview", response_model=ApiResponse[list[SecFilingMetadataCreate]])
def preview_company_filings(
    company_id: int,
    source: str = "auto",
    form_type: str | None = "10-K",
    filing_year: int | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
) -> ApiResponse[list[SecFilingMetadata]]:
    company = get_or_404(db, Company, company_id)
    provider = get_filing_provider(company, source=source)
    try:
        filings = provider.preview_filings(
            company,
            form_type=form_type,
            filing_year=filing_year,
            limit=limit,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Filing preview provider failed",
            extra={"provider": provider.provider_name, "exception_type": type(exc).__name__},
        )
        raise PublicApiError(
            status_code=502,
            code="FILING_PREVIEW_FAILED",
            message="Filing preview is temporarily unavailable.",
            retryable=True,
            provider=provider.provider_name,
        ) from exc
    return ApiResponse(data=filings, meta={"source": provider.provider_name})


@router.post(
    "/companies/{company_id}/filings/manual",
    response_model=ApiResponse[RawDocumentRead],
    status_code=status.HTTP_201_CREATED,
)
def add_manual_company_filing(
    company_id: int,
    payload: ManualFilingCreate,
    db: Session = Depends(get_db),
) -> ApiResponse[RawDocumentRead]:
    company = get_or_404(db, Company, company_id)
    return ApiResponse(data=create_manual_filing(db, company, payload))


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
        logger.error(
            "SEC filing preview failed",
            extra={"provider": "SEC EDGAR", "exception_type": type(exc).__name__},
        )
        raise PublicApiError(
            status_code=502,
            code="SEC_FILING_PREVIEW_FAILED",
            message="SEC filing preview is temporarily unavailable.",
            retryable=True,
            provider="SEC EDGAR",
        ) from exc

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

@router.get(
    "/companies/{company_id}/industry-mapping-candidates",
    response_model=ApiResponse[list[dict[str, Any]]],
)
def get_industry_mapping_candidates(company_id: int, country: str = "India", db: Session = Depends(get_db)):
    from app.services.industry_mapping import IndustryMappingService
    candidates = IndustryMappingService.suggest_damodaran_industries(db, company_id, country)
    return ApiResponse(data=candidates)

@router.get(
    "/industries/candidates",
    response_model=ApiResponse[list[str]],
)
def get_all_industry_candidates(country: str = "United States", db: Session = Depends(get_db)):
    from app.services.industry_mapping import IndustryMappingService
    exact_candidates = IndustryMappingService.get_available_industries(
        db,
        country,
        fallback_to_loaded=False,
    )
    candidates = exact_candidates or IndustryMappingService.get_available_industries(db, country)
    available_countries = IndustryMappingService.get_available_countries(db)
    warnings = []
    if candidates and not exact_candidates:
        loaded_country_text = ", ".join(available_countries) or "another market"
        warnings.append(
            f"No {country} industry taxonomy is loaded. Showing the classification names "
            f"from {loaded_country_text}; numeric valuation priors remain country-labeled."
        )
    return ApiResponse(
        data=candidates,
        meta={
            "source": "Damodaran benchmark taxonomy",
            "warnings": warnings,
            "confidence": "high" if exact_candidates else "medium",
        },
    )


@router.get(
    "/companies/{company_id}/industry-allocations",
    response_model=ApiResponse[CompanyIndustryMixRead],
)
def get_industry_allocations(company_id: int, db: Session = Depends(get_db)):
    from app.services.industry_mapping import IndustryMappingService

    get_or_404(db, Company, company_id)
    mix = IndustryMappingService.get_industry_mix(db, company_id)
    return ApiResponse(
        data=IndustryMappingService.serialize_industry_mix(db, mix) if mix is not None else None,
        meta={"source": "user_assumption", "confidence": "high"},
    )


@router.put(
    "/companies/{company_id}/industry-allocations",
    response_model=ApiResponse[CompanyIndustryMixRead],
)
def replace_industry_allocations(
    company_id: int,
    payload: CompanyIndustryMixUpdate,
    db: Session = Depends(get_db),
):
    from app.services.industry_mapping import IndustryMappingService

    try:
        mix = IndustryMappingService.save_industry_mix(
            db,
            company_id,
            **payload.model_dump(),
        )
    except ValueError as exc:
        raise PublicApiError(
            status_code=422,
            code="INDUSTRY_MIX_INVALID",
            message=str(exc),
            field="allocations",
        ) from exc
    return ApiResponse(
        data=IndustryMappingService.serialize_industry_mix(db, mix),
        meta={"source": "user_assumption", "confidence": "high"},
    )

@router.post("/companies/{company_id}/industry-mapping", response_model=ApiResponse[CompanyRead])
def update_industry_mapping(company_id: int, payload: dict, db: Session = Depends(get_db)):
    from app.services.industry_mapping import IndustryMappingService
    industry_name = payload.get("industry_name")
    if not industry_name:
        raise HTTPException(status_code=400, detail="industry_name is required")

    try:
        company = IndustryMappingService.confirm_industry_mapping(db, company_id, industry_name)
        return ApiResponse(data=company)
    except ValueError as exc:
        raise PublicApiError(
            status_code=422,
            code="INDUSTRY_MAPPING_INVALID",
            message="The industry mapping could not be confirmed.",
            field="industry_name",
        ) from exc

from fastapi.responses import Response

@router.get("/companies/{company_id}/memo", response_class=Response)
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
    return response
