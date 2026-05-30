from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.helpers import require_reference
from app.api.schemas import ApiResponse, FredIngestionCreate, FredIngestionRead, RssBatchIngestionRead, RssIngestionCreate, RssIngestionRead, SecFilingIngestionCreate, SecFilingIngestionRead
from app.core.config import get_settings
from app.db.session import get_db
from app.models import Company, ProcessingRun, Source
from app.services.ingestion_pipeline import PostIngestionPipelineResult, run_post_ingestion_pipeline
from app.services.macro_ingestion import ingest_fred_series
from app.services.processing_runs import record_ingestion_run
from app.services.rss_ingestion import RssIngestionResult, ingest_rss_feed_url, ingest_rss_xml
from app.services.sec_ingestion import SecFilingMetadata, SecIngestionResult, ingest_recent_sec_filings_for_company, ingest_sec_filing_metadata


router = APIRouter()


@router.get("/ingestion/status")
def get_ingestion_status(db: Session = Depends(get_db)) -> ApiResponse[dict[str, Any]]:
    runs = db.scalars(select(ProcessingRun).order_by(ProcessingRun.created_at.desc()).limit(10)).all()
    return ApiResponse(data={"latest_runs": [
        {
            "id": r.id,
            "run_type": r.run_type,
            "status": r.status,
            "started_at": r.started_at.isoformat(),
            "fetched_count": r.fetched_count,
            "error_count": r.error_count
        } for r in runs
    ]})

@router.post("/ingest/rss", response_model=ApiResponse[RssIngestionRead], status_code=status.HTTP_201_CREATED)
def ingest_rss(payload: RssIngestionCreate, db: Session = Depends(get_db)) -> dict[str, int | list[str]]:
    require_reference(db, Source, payload.source_id, "Source")
    require_reference(db, Company, payload.company_id, "Company")
    if payload.rss_xml is None:
        raise HTTPException(status_code=422, detail="rss_xml is required")
    started_at = datetime.now(UTC)
    result = ingest_rss_xml(db, source_id=payload.source_id, rss_xml=payload.rss_xml, company_id=payload.company_id)
    record_ingestion_run_for_result(
        db,
        run_type="rss_ingestion",
        source_id=payload.source_id,
        company_id=payload.company_id,
        result=result,
        started_at=started_at,
    )
    return ApiResponse(data=rss_ingestion_response(result, run_pipeline_if_needed(db, result.created_count)))


@router.post("/ingest/rss-feed", response_model=ApiResponse[RssIngestionRead], status_code=status.HTTP_201_CREATED)
def ingest_rss_feed(payload: RssIngestionCreate, db: Session = Depends(get_db)) -> dict[str, int | list[str]]:
    require_reference(db, Source, payload.source_id, "Source")
    require_reference(db, Company, payload.company_id, "Company")
    started_at = datetime.now(UTC)
    result = ingest_rss_feed_url(db, source_id=payload.source_id, feed_url=payload.feed_url, company_id=payload.company_id)
    record_ingestion_run_for_result(
        db,
        run_type="rss_ingestion",
        source_id=payload.source_id,
        company_id=payload.company_id,
        result=result,
        started_at=started_at,
    )
    return ApiResponse(data=rss_ingestion_response(result, run_pipeline_if_needed(db, result.created_count)))


@router.post("/ingest/rss-feeds/active", response_model=ApiResponse[RssBatchIngestionRead], status_code=status.HTTP_201_CREATED)
def ingest_active_rss_feeds(db: Session = Depends(get_db)) -> dict[str, int | list[str]]:
    sources = list(
        db.scalars(
            select(Source)
            .where(Source.source_type == "rss", Source.active.is_(True), Source.base_url.is_not(None))
            .order_by(Source.id)
        )
    )
    response: dict[str, int | list[str]] = _empty_rss_batch_response(source_count=len(sources))

    for source in sources:
        started_at = datetime.now(UTC)
        result = ingest_rss_feed_url(db, source_id=source.id)
        record_ingestion_run_for_result(
            db,
            run_type="rss_ingestion",
            source_id=source.id,
            company_id=None,
            result=result,
            started_at=started_at,
            metadata={"mode": "active_rss_feed_batch"},
        )
        pipeline = run_pipeline_if_needed(db, result.created_count)
        _add_rss_result_to_batch_response(response, source, result, pipeline)

    return ApiResponse(data=response)


@router.post("/ingest/sec-filings", response_model=ApiResponse[SecFilingIngestionRead], status_code=status.HTTP_201_CREATED)
def ingest_sec_filings(payload: SecFilingIngestionCreate, db: Session = Depends(get_db)) -> dict[str, int | list[str]]:
    require_reference(db, Source, payload.source_id, "Source")
    require_reference(db, Company, payload.company_id, "Company")
    filings = [
        SecFilingMetadata(
            accession_number=filing.accession_number,
            form_type=filing.form_type,
            filing_date=filing.filing_date,
            report_date=filing.report_date,
            primary_document=filing.primary_document,
            filing_url=filing.filing_url,
        )
        for filing in payload.filings
    ]
    started_at = datetime.now(UTC)
    result = ingest_sec_filing_metadata(
        db,
        source_id=payload.source_id,
        company_id=payload.company_id,
        filings=filings,
        download_text=payload.download_text,
    )
    record_ingestion_run_for_result(
        db,
        run_type="sec_ingestion",
        source_id=payload.source_id,
        company_id=payload.company_id,
        result=result,
        started_at=started_at,
        metadata={"form_types": list(payload.form_types), "download_text": payload.download_text},
    )
    return ApiResponse(data=sec_ingestion_response(result, run_pipeline_if_needed(db, result.created_count)))


@router.post("/ingest/sec-filings/recent", response_model=ApiResponse[SecFilingIngestionRead], status_code=status.HTTP_201_CREATED)
def ingest_recent_sec_filings(payload: SecFilingIngestionCreate, db: Session = Depends(get_db)) -> dict[str, int | list[str]]:
    require_reference(db, Source, payload.source_id, "Source")
    require_reference(db, Company, payload.company_id, "Company")
    started_at = datetime.now(UTC)
    result = ingest_recent_sec_filings_for_company(
        db,
        source_id=payload.source_id,
        company_id=payload.company_id,
        form_types=tuple(payload.form_types),
        filing_year=payload.filing_year,
        limit=payload.limit,
        download_text=payload.download_text,
    )
    record_ingestion_run_for_result(
        db,
        run_type="sec_ingestion",
        source_id=payload.source_id,
        company_id=payload.company_id,
        result=result,
        started_at=started_at,
        metadata={
            "form_types": list(payload.form_types),
            "filing_year": payload.filing_year,
            "limit": payload.limit,
            "mode": "recent",
            "download_text": payload.download_text,
        },
    )
    return ApiResponse(data=sec_ingestion_response(result, run_pipeline_if_needed(db, result.created_count)))


@router.post("/ingest/fred-series", response_model=ApiResponse[FredIngestionRead], status_code=status.HTTP_201_CREATED)
def ingest_fred(payload: FredIngestionCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    settings = get_settings()
    if not settings.fred_api_key:
        raise HTTPException(status_code=400, detail="FRED API key not configured in environment.")
    
    try:
        result = ingest_fred_series(db, payload.series_id, api_key=settings.fred_api_key)
        return ApiResponse(data=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


def run_pipeline_if_needed(db: Session, created_count: int) -> ApiResponse[PostIngestionPipelineResult | None]:
    # Always run the pipeline so that if a threshold changes, existing events can generate alerts
    return ApiResponse(data=run_post_ingestion_pipeline(db))


def record_ingestion_run_for_result(
    db: Session,
    *,
    run_type: str,
    source_id: int,
    company_id: int | None,
    result: RssIngestionResult | SecIngestionResult,
    started_at: datetime | None = None,
    metadata: dict | None = None,
) -> ApiResponse[ProcessingRun]:
    source = db.get(Source, source_id)
    return ApiResponse(data=record_ingestion_run(
        db,
        run_type=run_type,
        source_type=source.source_type if source is not None else None,
        source_id=source_id,
        company_id=company_id,
        result=result,
        started_at=started_at,
        metadata=metadata,
    ))


def rss_ingestion_response(result: RssIngestionResult, pipeline: PostIngestionPipelineResult | None = None) -> ApiResponse[dict[str, int | list[str]]]:
    response: dict[str, int | list[str]] = {
        "fetched_count": result.fetched_count,
        "created_count": result.created_count,
        "skipped_duplicate_count": result.skipped_duplicate_count,
        "error_count": result.error_count,
        "errors": list(result.errors),
        "created": result.created,
        "skipped_duplicates": result.skipped_duplicates,
    }
    return ApiResponse(data=response | pipeline_response(pipeline))


def _empty_rss_batch_response(source_count: int) -> ApiResponse[dict[str, int | list[str]]]:
    return ApiResponse(data={
        "source_count": source_count,
        "fetched_count": 0,
        "created_count": 0,
        "skipped_duplicate_count": 0,
        "error_count": 0,
        "errors": [],
        "created": 0,
        "skipped_duplicates": 0,
        "events_created": 0,
        "events_skipped_existing": 0,
        "alerts_created": 0,
        "alerts_skipped_existing": 0,
        "alerts_skipped_below_threshold": 0,
    })


def _add_rss_result_to_batch_response(
    response: dict[str, int | list[str]],
    source: Source,
    result: RssIngestionResult,
    pipeline: PostIngestionPipelineResult | None,
) -> ApiResponse[None]:
    response["fetched_count"] += result.fetched_count
    response["created_count"] += result.created_count
    response["skipped_duplicate_count"] += result.skipped_duplicate_count
    response["error_count"] += result.error_count
    response["created"] += result.created
    response["skipped_duplicates"] += result.skipped_duplicates
    response["errors"].extend(f"{source.name}: {error}" for error in result.errors)
    pipeline_counts = pipeline_response(pipeline)
    for key, value in pipeline_counts.items():
        response[key] += value


def sec_ingestion_response(result: SecIngestionResult, pipeline: PostIngestionPipelineResult | None = None) -> ApiResponse[dict[str, int | list[str]]]:
    response: dict[str, int | list[str]] = {
        "fetched_count": result.fetched_count,
        "created_count": result.created_count,
        "skipped_duplicate_count": result.skipped_duplicate_count,
        "error_count": result.error_count,
        "errors": list(result.errors),
        "created": result.created,
        "skipped_duplicates": result.skipped_duplicates,
    }
    return ApiResponse(data=response | pipeline_response(pipeline))


def pipeline_response(pipeline: PostIngestionPipelineResult | None) -> ApiResponse[dict[str, int]]:
    if pipeline is None:
        return ApiResponse(data={
            "events_created": 0,
            "events_skipped_existing": 0,
            "alerts_created": 0,
            "alerts_skipped_existing": 0,
            "alerts_skipped_below_threshold": 0,
        })
    return ApiResponse(data={
        "events_created": pipeline.event_extraction.created,
        "events_skipped_existing": pipeline.event_extraction.skipped_existing,
        "alerts_created": pipeline.alert_generation.created,
        "alerts_skipped_existing": pipeline.alert_generation.skipped_existing,
        "alerts_skipped_below_threshold": pipeline.alert_generation.skipped_below_threshold,
    })
