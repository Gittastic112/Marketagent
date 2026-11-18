from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime
from typing import Callable

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Company, DocumentAsset, FinancialExtractionCandidate, RawDocument, Source
from app.models.company_setup import CompanySetupWorkflow
from app.providers.extraction.jobs import dependency_version, run_extraction
from app.providers.filings.india_metadata import assert_filing_identity, normalize_india_filing
from app.providers.fred_provider import FredProvider
from app.providers.research_sources.errors import SourceAdapterError
from app.providers.research_sources.transcripts import fetch_transcript
from app.schemas.source_adapters import (DocumentExtractionRequest, FredVintageRequest, IndiaFilingsRequest,
    SecFactsAdapterRequest, SourceAdapterResult, TranscriptRequest)
from app.services.processing_runs import fail_processing_run, start_processing_run
from app.services.sec_xbrl_extractor import company_sec_cik, fetch_company_facts


def _json_bytes(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def _company(db: Session, company_id: int) -> Company:
    company = db.scalar(select(Company).where(Company.id == company_id).with_for_update())
    if company is None:
        raise SourceAdapterError("COMPANY_NOT_FOUND", "Company not found.", 404)
    return company


def _source(db: Session, adapter: str, url: str | None) -> Source:
    name = f"Source adapter: {adapter}"
    source = db.scalar(select(Source).where(Source.name == name))
    if source is None:
        try:
            with db.begin_nested():
                source = Source(name=name, source_type="research_adapter", base_url=url, reliability_score=None)
                db.add(source)
                db.flush()
        except IntegrityError:
            source = db.scalar(select(Source).where(Source.name == name))
            if source is None:
                raise
    return source


def _document(db: Session, *, adapter: str, company_id: int | None, record_id: str,
              title: str, kind: str, raw_payload: dict | list, metadata: dict,
              observed_at: datetime, text: str | None = None, url: str | None = None,
              published_at: datetime | None = None) -> tuple[RawDocument, bool]:
    digest = hashlib.sha256(_json_bytes({"record_id": record_id, "payload": raw_payload})).hexdigest()
    payload_sha256 = hashlib.sha256(_json_bytes(raw_payload)).hexdigest()
    identity = f"source-adapter:{adapter}:{company_id}:{digest}"
    existing = db.scalar(select(RawDocument).where(RawDocument.content_hash == identity))
    if existing is not None:
        return existing, False
    previous = db.scalar(select(RawDocument).where(RawDocument.company_id == company_id,
        RawDocument.raw_payload_json["adapter"].as_string() == adapter,
        RawDocument.raw_payload_json["provider_record_id"].as_string() == record_id).order_by(RawDocument.id.desc()).limit(1))
    source = _source(db, adapter, url)
    document = RawDocument(company_id=company_id, source_id=source.id, document_type=kind,
        title=title[:500], url=url, published_at=published_at, raw_text=text, content_hash=identity,
        raw_payload_json={**metadata, "source_kind": "source_adapter", "adapter": adapter,
            "provider_record_id": record_id, "payload_sha256": payload_sha256, "observed_at": observed_at.isoformat(),
            "publication_time_known": published_at is not None, "raw_response": raw_payload,
            "supersedes_raw_document_id": previous.id if previous else None})
    try:
        with db.begin_nested():
            db.add(document)
            db.flush()  # Makes retries within the same batch visible with autoflush=False.
    except IntegrityError:
        existing = db.scalar(select(RawDocument).where(RawDocument.content_hash == identity))
        if existing is None:
            raise
        return existing, False
    return document, True


def _audit_request(adapter: str, parameters: dict | None, company: Company | None) -> dict:
    allowed = {
        "edgartools": {"as_of", "max_years"},
        "camelot": {"adapter", "pages", "document_id"},
        "docling": {"adapter", "pages", "document_id"},
        "marker": {"adapter", "pages", "document_id"},
        "alfred": {"series_id", "as_of", "observation_start", "observation_end", "mode", "max_pages"},
        "earningscall": {"provider", "fiscal_year", "fiscal_quarter", "exchange", "level"},
        "fmp": {"provider", "fiscal_year", "fiscal_quarter", "exchange", "level"},
        "india_nse": {"exchange", "record_count"},
        "india_bse": {"exchange", "record_count"},
    }.get(adapter, set())
    context = {"parameters": {key: value for key, value in (parameters or {}).items() if key in allowed}}
    if company is not None:
        context["company_listing"] = {"company_id": company.id, "market": company.market,
            "ticker": company.ticker, "local_symbol": company.local_symbol, "provider_symbol": company.local_symbol or company.ticker,
            "primary_exchange": company.primary_exchange, "currency": company.currency, "cik": company.cik,
            "regulatory_id": company.regulatory_id, "regulatory_id_type": company.regulatory_id_type,
            "isin": company.isin, "figi": company.figi}
        if adapter in {"earningscall", "fmp"}:
            context["company_listing"]["resolved_listing_exchange"] = (parameters or {}).get("exchange") or company.primary_exchange
    encoded = _json_bytes(context)
    if len(encoded) > 8192:
        raise SourceAdapterError("AUDIT_CONTEXT_TOO_LARGE", "Source request context exceeds its supported limit.")
    return json.loads(encoded)  # Freeze the request independently of mutable inputs.


def audited_action(db: Session, *, adapter: str, company_id: int | None, user_id: str,
                   action: Callable[[], SourceAdapterResult], request_context: dict | None = None) -> SourceAdapterResult:
    company = db.get(Company, company_id) if company_id is not None else None
    if company_id is not None and company is None:
        raise SourceAdapterError("COMPANY_NOT_FOUND", "Company not found.", 404)
    run = start_processing_run(db, run_type="source_adapter", source_type="research_adapter",
        company_id=company_id, metadata={"adapter": adapter, "user_id": user_id,
            "request_context": _audit_request(adapter, request_context, company)})
    try:
        result = action()
        useful = bool(result.created_count or result.duplicate_count or result.raw_document_ids or result.candidate_ids)
        if result.status == "partial" and not useful:
            result.status = "unavailable"
        # Evidence can be useful without being new. The generic completion helper
        # treats zero-created partial runs as failed, which is wrong for repeats.
        run.status = {"success": "success", "partial": "partial_success", "unavailable": "failed"}[result.status]
        run.fetched_count, run.created_count = result.fetched_count, result.created_count
        run.skipped_duplicate_count = result.duplicate_count
        run.error_count = int(result.status != "success")
        run.error_details_json = {"errors": result.warnings} if run.error_count else None
        run.metadata_json = {**(run.metadata_json or {}), "raw_document_ids": result.raw_document_ids,
            "candidate_ids": result.candidate_ids, "warnings": result.warnings, "adapter_status": result.status}
        run.finished_at = datetime.now(UTC)
        db.commit()
        db.refresh(run)
        result.processing_run_id = run.id
        return result
    except Exception as error:
        db.rollback()
        safe = error if isinstance(error, SourceAdapterError) else SourceAdapterError(
            "SOURCE_ADAPTER_FAILED", "The source adapter could not complete this action.", 502)
        fail_processing_run(db, run, error_type=safe.code, message=str(safe))
        safe.processing_run_id = run.id
        raise safe from None


def intake_india_filings(db: Session, company_id: int, request: IndiaFilingsRequest) -> SourceAdapterResult:
    company = _company(db, company_id)
    if company.market != "IN":
        raise SourceAdapterError("MARKET_MISMATCH", "India filing intake requires an Indian company.")
    symbol = company.local_symbol or company.ticker
    scrip = symbol if symbol.isdigit() and company.primary_exchange in {"BSE", "XBOM"} else (
        company.regulatory_id if company.regulatory_id_type == "BSE_SCRIP_CODE" else None)
    normalized = [normalize_india_filing(request.exchange, row) for row in request.records]
    for item in normalized:
        assert_filing_identity(item, symbol=symbol, isin=company.isin, scrip_code=scrip)
    now, document_ids, created, warnings = datetime.now(UTC), [], 0, set()
    for item in normalized:
        metadata = item.model_dump(mode="json", exclude={"raw_payload"})
        document, is_new = _document(db, adapter=f"india_{request.exchange.lower()}", company_id=company_id,
            record_id=item.provider_record_id, title=item.title, kind=item.document_type, raw_payload=item.raw_payload,
            metadata={"filing_metadata": metadata, "claim_type": "Source Summary", "intake_method": "user_supplied_original_metadata"},
            observed_at=now, url=item.attachment_url, published_at=item.published_at)
        document_ids.append(document.id)
        created += is_new
        warnings.update(item.warnings)
    return SourceAdapterResult(adapter=f"india_{request.exchange.lower()}", raw_document_ids=list(dict.fromkeys(document_ids)),
        fetched_count=len(normalized), created_count=created, duplicate_count=len(normalized) - created,
        observed_at=now, warnings=sorted(warnings), details={"network_requests": 0, "attachments_downloaded": False})


def ingest_transcript(db: Session, company_id: int, request: TranscriptRequest, *, api_key: str | None) -> SourceAdapterResult:
    company = _company(db, company_id)
    exchange = request.exchange or company.primary_exchange
    if request.exchange and company.primary_exchange and request.exchange != company.primary_exchange:
        raise SourceAdapterError("EXCHANGE_MISMATCH", "The requested exchange does not match the selected listing.")
    if request.provider == "fmp" and (company.market != "US" or company.primary_exchange not in {
            "NASDAQ", "NYSE", "AMEX", "NYSEAMERICAN", "XNAS", "XNYS", "XASE"}):
        raise SourceAdapterError("FMP_TRANSCRIPT_LISTING_UNSUPPORTED",
            "FMP transcript intake requires a resolved supported US listing; international ticker mapping is not verified.")
    evidence = fetch_transcript(request=request, symbol=company.local_symbol or company.ticker,
        exchange=exchange, api_key=api_key)
    metadata = evidence.model_dump(mode="json", exclude={"raw_payload", "text"})
    document, created = _document(db, adapter=request.provider, company_id=company_id,
        record_id=evidence.provider_record_id, title=f"{company.ticker} FY{request.fiscal_year} Q{request.fiscal_quarter} earnings transcript",
        kind="earnings_transcript", raw_payload=evidence.raw_payload, metadata={"transcript": metadata, "claim_type": "Source Summary"},
        observed_at=evidence.observed_at, text=evidence.text,
        url="https://earningscall.biz" if request.provider == "earningscall" else "https://financialmodelingprep.com",
        published_at=evidence.published_at)
    return SourceAdapterResult(adapter=request.provider, raw_document_ids=[document.id], fetched_count=1,
        created_count=int(created), duplicate_count=int(not created), observed_at=evidence.observed_at,
        warnings=evidence.warnings, details={"segments": len(evidence.segments), "api_version": evidence.api_version,
                                          "historical_availability": "unknown"})


def ingest_fred_vintage(db: Session, request: FredVintageRequest, *, api_key: str | None) -> SourceAdapterResult:
    if not api_key:
        raise SourceAdapterError("PROVIDER_NOT_CONFIGURED", "FRED is not configured.", 503)
    result = FredProvider(api_key).fetch_vintage_observations(request.series_id, as_of=request.as_of,
        observation_start=request.observation_start, observation_end=request.observation_end,
        mode=request.mode, max_pages=request.max_pages)
    now = datetime.now(UTC)
    record_id = f"{request.series_id.upper()}:{request.mode}:{request.as_of}:{request.observation_start}:{request.observation_end}"
    document, created = _document(db, adapter="alfred", company_id=None, record_id=record_id,
        title=f"{request.series_id.upper()} ALFRED vintage {request.as_of}", kind="macro_vintage",
        raw_payload=result["raw_pages"], metadata={"vintage": {k: v for k, v in result.items() if k != "raw_pages"},
            "request": request.model_dump(mode="json"), "claim_type": "Source Summary"}, observed_at=now,
        url=f"https://fred.stlouisfed.org/series/{request.series_id.upper()}")
    return SourceAdapterResult(adapter="alfred", raw_document_ids=[document.id], fetched_count=result["fetched_count"],
        created_count=int(created), duplicate_count=int(not created), observed_at=now,
        status="success" if result["complete"] else "partial", warnings=result["warnings"],
        details={"observations": result["observations"], "as_of": str(request.as_of), "mode": request.mode,
                 "complete": result["complete"], "current_macro_values_modified": False})


def _store_candidates(db: Session, company: Company, document: RawDocument, data: dict,
                       adapter: str, payload_hash: str) -> tuple[list[int], int]:
    method = f"pdf_{adapter}_adapter_v1" if adapter != "edgartools" else "edgartools_companyfacts_v1"
    existing = db.scalars(select(FinancialExtractionCandidate).where(
        FinancialExtractionCandidate.raw_document_id == document.id,
        FinancialExtractionCandidate.extraction_method == method)).all()
    existing_keys = {row.source_locator_json.get("adapter_candidate_hash"): row.id for row in existing}
    created_ids, duplicates = [], 0
    for item in data["candidates"]:
        stable = {**item, "source_locator_json": {key: value for key, value in item["source_locator_json"].items() if key != "as_of"}}
        identity = hashlib.sha256(_json_bytes(stable)).hexdigest()
        if identity in existing_keys:
            duplicates += 1
            continue
        locator = {**item["source_locator_json"], "payload_sha256": payload_hash, "source_url": document.url,
            "adapter_candidate_hash": identity, "adapter_version": data["dependency_version"]}
        fields = {key: value for key, value in item.items() if key != "source_locator_json"}
        candidate = FinancialExtractionCandidate(company_id=company.id, raw_document_id=document.id,
            **fields, source_locator_json=locator, extraction_method=method, review_status="needs_review")
        db.add(candidate)
        db.flush()
        existing_keys[identity] = candidate.id
        created_ids.append(candidate.id)
    if created_ids:
        workflow = db.scalar(select(CompanySetupWorkflow).where(CompanySetupWorkflow.company_id == company.id))
        if workflow is not None:
            workflow.financial_extraction_status = "needs_review"
            workflow.current_step = "financial_review"
    return created_ids, duplicates


def extract_sec_facts(db: Session, company_id: int, request: SecFactsAdapterRequest, *, user_agent: str) -> SourceAdapterResult:
    if not dependency_version("edgartools"):
        raise SourceAdapterError("EXTRACTION_DEPENDENCY_MISSING", "The optional edgartools dependency is not installed.", 503)
    company = _company(db, company_id)
    cik = company_sec_cik(company)
    if not cik or company.market != "US":
        raise SourceAdapterError("SEC_IDENTITY_REQUIRED", "SEC extraction requires a US issuer with a verified CIK.")
    if not company.currency:
        raise SourceAdapterError("REPORTING_CURRENCY_REQUIRED", "Configure the company's reporting currency before extraction.")
    cutoff = request.as_of or date.today()
    if cutoff > date.today():
        raise SourceAdapterError("INVALID_CUTOFF", "The source cutoff cannot be future dated.")
    payload = fetch_company_facts(cik, user_agent=user_agent)
    data = run_extraction("edgartools", _json_bytes(payload), options={"as_of": cutoff.isoformat(),
        "currency": company.currency.upper(), "max_years": request.max_years})
    now = datetime.now(UTC)
    document, created = _document(db, adapter="edgartools", company_id=company_id, record_id=f"CIK{int(cik):010d}",
        title=f"{company.ticker} SEC company facts", kind="xbrl_facts", raw_payload=payload,
        metadata={"companyfacts": payload, "dependency_version": data["dependency_version"]}, observed_at=now,
        url=f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json")
    ids, duplicates = _store_candidates(db, company, document, data, "edgartools", document.raw_payload_json["payload_sha256"])
    return SourceAdapterResult(adapter="edgartools", raw_document_ids=[document.id], candidate_ids=ids,
        fetched_count=data["fetched_count"], created_count=len(ids), duplicate_count=duplicates, observed_at=now,
        warnings=data["warnings"], details={"source_created": created, "excluded_count": data["excluded_count"],
            "fiscal_years": data["fiscal_years"], "missing_core_metrics_by_year": data["missing_core_metrics_by_year"],
            "dependency_version": data["dependency_version"], "as_of": cutoff.isoformat()})


def extract_stored_pdf(db: Session, company_id: int, document_id: int, request: DocumentExtractionRequest,
                       *, model_dir: str | None, python_executable: str | None = None) -> SourceAdapterResult:
    company = _company(db, company_id)
    document = db.get(RawDocument, document_id)
    if document is None or document.company_id != company_id:
        raise SourceAdapterError("SOURCE_NOT_FOUND", "Company source document not found.", 404)
    asset = db.scalar(select(DocumentAsset).where(DocumentAsset.raw_document_id == document_id))
    if asset is None or asset.mime_type != "application/pdf":
        raise SourceAdapterError("PDF_ASSET_REQUIRED", "The original stored PDF asset is required.")
    digest = hashlib.sha256(asset.content).hexdigest()
    if digest != asset.sha256 or len(asset.content) != asset.size_bytes:
        raise SourceAdapterError("SOURCE_INTEGRITY_FAILED", "Original source bytes do not match the stored evidence hash.", 409)
    period_type = "annual" if document.document_type in {"annual_report", "10-K", "10-K/A"} else (
        "quarterly" if document.document_type in {"quarterly_result", "10-Q", "10-Q/A"} else "unknown")
    data = run_extraction(request.adapter, asset.content, pages=request.pages, model_dir=model_dir,
        options={"period_type": period_type}, python_executable=python_executable if request.adapter in {"docling", "marker"} else None)
    ids, duplicates = _store_candidates(db, company, document, data, request.adapter, digest)
    return SourceAdapterResult(adapter=request.adapter, raw_document_ids=[document_id], candidate_ids=ids,
        fetched_count=data["table_count"], created_count=len(ids), duplicate_count=duplicates, observed_at=datetime.now(UTC),
        warnings=data["warnings"], details={"scanned_pages": data["scanned_pages"], "page_count": data["page_count"],
            "dependency_version": data["dependency_version"], "original_asset_modified": False})
