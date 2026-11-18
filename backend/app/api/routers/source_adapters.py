"""Authenticated explicit source actions; reading capabilities never fetches data."""
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.providers.extraction.jobs import PACKAGES, dependency_version, extraction_dependency_conflict
from app.providers.research_sources.errors import SourceAdapterError
from app.schemas.common import ApiErrorDetail, ApiMeta, ApiResponse
from app.schemas.source_adapters import (DocumentExtractionRequest, FredVintageRequest, IndiaFilingsRequest,
    SecFactsAdapterRequest, SourceAdapterCapability, SourceAdapterResult, TranscriptRequest)
from app.services.source_adapters.workflows import (audited_action, extract_sec_facts, extract_stored_pdf,
    ingest_fred_vintage, ingest_transcript, intake_india_filings)

router = APIRouter(tags=["source_adapters"], dependencies=[Depends(get_current_user)])


def _run(db, user, adapter, company_id, action, *, request_context=None):
    try:
        result = audited_action(db, adapter=adapter, company_id=company_id, user_id=user["id"], action=action,
            request_context=request_context)
        return ApiResponse(data=result, meta=ApiMeta(source=adapter, status=result.status,
            last_updated=result.observed_at, warnings=result.warnings, confidence="medium"))
    except SourceAdapterError as error:
        envelope = ApiResponse(data=None, meta=ApiMeta(source=adapter, status="unavailable"),
            errors=[ApiErrorDetail(code=error.code, message=str(error), retryable=error.retryable,
                provider=adapter, processing_run_id=getattr(error, "processing_run_id", None))])
        return JSONResponse(status_code=error.status_code, content=envelope.model_dump(mode="json"))


@router.get("/api/source-adapters", response_model=ApiResponse[list[SourceAdapterCapability]])
def source_capabilities():
    settings = get_settings()
    result = []
    for adapter in PACKAGES:
        worker_python = getattr(settings, "source_adapter_python", None) if adapter in {"docling", "marker"} else None
        version = dependency_version(adapter, worker_python)
        conflict = extraction_dependency_conflict(adapter, worker_python) if version else None
        model_dir = getattr(settings, "source_adapter_model_dir", None)
        models = adapter not in {"docling", "marker"} or bool(model_dir and Path(model_dir).is_dir())
        warnings = ["Runtime compatibility and source extraction are established by individual runs."]
        if adapter == "marker":
            warnings.append("Marker 2.2.0 is excluded from the approved OCR profile because its published dependency stack conflicts with the safe Pillow/filelock versions.")
        if conflict:
            warnings.append(conflict)
        result.append(SourceAdapterCapability(adapter=adapter, available=bool(version and models and not conflict),
            dependency_version=version, status="dependency_conflict" if conflict else "ready_to_attempt" if version and models else "dependency_missing" if not version else "models_missing",
            warnings=warnings))
    for adapter, configured in (("earningscall", bool(getattr(settings, "earningscall_api_key", None))),
        ("fmp", bool(settings.fmp_api_key)), ("alfred", bool(settings.fred_api_key))):
        result.append(SourceAdapterCapability(adapter=adapter, available=configured,
            status="configured_not_live_verified" if configured else "not_configured"))
    result.extend(SourceAdapterCapability(adapter=name, available=True, status="offline_metadata_intake")
                  for name in ("india_nse", "india_bse"))
    return ApiResponse(data=result)


@router.post("/api/companies/{company_id}/source-adapters/sec-facts", response_model=ApiResponse[SourceAdapterResult])
def sec_facts(company_id: int, payload: SecFactsAdapterRequest, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    payload = payload.model_copy(update={"as_of": payload.as_of or date.today()})
    return _run(db, user, "edgartools", company_id,
        lambda: extract_sec_facts(db, company_id, payload, user_agent=get_settings().sec_user_agent),
        request_context=payload.model_dump(mode="json"))


@router.post("/api/companies/{company_id}/source-adapters/india-filings", response_model=ApiResponse[SourceAdapterResult])
def india_filings(company_id: int, payload: IndiaFilingsRequest, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return _run(db, user, f"india_{payload.exchange.lower()}", company_id, lambda: intake_india_filings(db, company_id, payload),
        request_context={"exchange": payload.exchange, "record_count": len(payload.records)})


@router.post("/api/companies/{company_id}/source-adapters/transcript", response_model=ApiResponse[SourceAdapterResult])
def transcript(company_id: int, payload: TranscriptRequest, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    settings = get_settings()
    key = getattr(settings, "earningscall_api_key", None) if payload.provider == "earningscall" else settings.fmp_api_key
    return _run(db, user, payload.provider, company_id, lambda: ingest_transcript(db, company_id, payload, api_key=key),
        request_context=payload.model_dump(mode="json"))


@router.post("/api/source-adapters/fred-vintage", response_model=ApiResponse[SourceAdapterResult])
def fred_vintage(payload: FredVintageRequest, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return _run(db, user, "alfred", None, lambda: ingest_fred_vintage(db, payload, api_key=get_settings().fred_api_key),
        request_context=payload.model_dump(mode="json"))


@router.post("/api/companies/{company_id}/source-adapters/documents/{document_id}/extract", response_model=ApiResponse[SourceAdapterResult])
def document_extract(company_id: int, document_id: int, payload: DocumentExtractionRequest,
                     db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return _run(db, user, payload.adapter, company_id,
        lambda: extract_stored_pdf(db, company_id, document_id, payload, model_dir=getattr(get_settings(), "source_adapter_model_dir", None),
            python_executable=getattr(get_settings(), "source_adapter_python", None)),
        request_context={"document_id": document_id, **payload.model_dump(mode="json")})
