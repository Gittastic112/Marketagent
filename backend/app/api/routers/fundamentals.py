import hashlib
import os
import tempfile
from pathlib import Path
from typing import Sequence
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy import select
from sqlalchemy.orm import Session

import app.api.schemas as schemas
from app.db.session import get_db
from app.models.financial import (
    FinancialExtractionCandidate,
    FinancialMetric,
    FinancialStatementPeriod,
    NormalizedFinancialSnapshot,
)
from app.models.company import Company
from app.models.processing_run import ProcessingRun
from app.models.raw_document import RawDocument
from app.models.source import Source
from app.api.schemas import ApiResponse, FinancialExtractionCandidateRead, FinancialExtractionResultRead, FinancialPeriodRead
from app.api.errors import PublicApiError
from app.services.financial_extraction import (
    extract_financial_candidates_from_filing,
    list_extracted_financial_candidates,
    update_candidate_review_status,
    override_candidate_value,
    promote_reviewed_candidates,
)
from app.services.accounting_normalization import (
    FinancialReconciliationService,
    MetricNormalizationEngine,
    NormalizedSnapshotBackfillService,
)
from app.services.sec_xbrl_ingestion import XbrlIngestionError, ingest_xbrl_candidates
from app.services.financial_statement_identity import FinancialStatementIdentityService
from app.services.processing_runs import complete_processing_run, fail_processing_run, start_processing_run
from app.providers.fundamentals.screener import ScreenerExcelParser
from app.services.workbook_safety import validate_workbook_bytes

router = APIRouter(tags=["fundamentals"])


@router.post(
    "/api/filings/{filing_id}/extract-financials",
    response_model=ApiResponse[FinancialExtractionResultRead],
    status_code=status.HTTP_201_CREATED,
)
def extract_financials_from_filing(filing_id: int, db: Session = Depends(get_db)) -> ApiResponse[FinancialExtractionResultRead]:
    document = db.get(RawDocument, filing_id)
    run = start_processing_run(
        db,
        run_type="filing_financial_extraction",
        source_type="filing",
        source_id=document.source_id if document else None,
        company_id=document.company_id if document else None,
        metadata={"raw_document_id": filing_id, "extraction_method": "regex_line_item_v1"},
    )
    try:
        result = extract_financial_candidates_from_filing(db, filing_id)
    except HTTPException as exc:
        db.rollback()
        fail_processing_run(
            db,
            run,
            error_type="request_error",
            message=str(exc.detail),
        )
        raise
    except Exception as exc:
        db.rollback()
        fail_processing_run(db, run, error_type=type(exc).__name__)
        raise
    complete_processing_run(
        db,
        run,
        fetched_count=result.created_count + result.skipped_existing_count,
        created_count=result.created_count,
        skipped_duplicate_count=result.skipped_existing_count,
    )
    return ApiResponse(data=result)


@router.post(
    "/api/companies/{company_id}/extract-xbrl",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_201_CREATED,
)
def extract_financials_from_xbrl(company_id: int, db: Session = Depends(get_db)):
    return _xbrl_response(db, company_id)


def _xbrl_response(db: Session, company_id: int, *, legacy: bool = False):
    try:
        result = ingest_xbrl_candidates(db, company_id,
            run_type="fundamentals_ingestion" if legacy else "sec_xbrl_extraction")
    except XbrlIngestionError as exc:
        raise PublicApiError(status_code=502, code="SEC_FACTS_INGESTION_FAILED",
            message="SEC company facts ingestion failed.", retryable=True,
            provider="SEC", processing_run_id=exc.processing_run_id) from None
    response = ApiResponse(data={"status": "success", **result})
    response.meta.warnings.extend(result.get("warnings", []))
    if legacy:
        # Preserve the old response field without claiming candidate intake updated facts.
        response.data.update(periods_updated=0, review_required=True)
        response.meta.warnings.append(
            "SEC intake creates review candidates only. Review and promote candidates before financial values change."
        )
    return response


@router.post(
    "/api/companies/{company_id}/fundamentals/screener",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_201_CREATED,
)
def ingest_screener_excel(
    company_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    allowed_mime_types = {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/octet-stream",
    }
    filename = Path(file.filename or "screener-upload.xlsx").name
    if file.content_type not in allowed_mime_types or not filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only Excel .xlsx files are allowed.")

    temp_path: str | None = None
    processing_run_id: int | None = None
    try:
        content = file.file.read(2 * 1024 * 1024 + 1)
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        if len(content) > 2 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 2MB.")
        validate_workbook_bytes(content)

        digest = hashlib.sha256(content).hexdigest()
        content_hash = f"screener-upload:{digest}"

        source = db.scalar(select(Source).where(Source.name == "Screener.in Uploads"))
        if source is None:
            source = Source(
                name="Screener.in Uploads",
                source_type="manual_financial_upload",
                base_url="https://www.screener.in",
                reliability_score=70,
                active=True,
            )
            db.add(source)
            db.flush()

        processing_run = start_processing_run(
            db,
            run_type="screener_upload",
            source_type=source.source_type,
            source_id=source.id,
            company_id=company_id,
            fetched_count=1,
            metadata={
                "original_filename": filename,
                "file_size_bytes": len(content),
                "sha256": digest,
            },
        )
        processing_run_id = processing_run.id

        if db.scalar(select(RawDocument).where(RawDocument.content_hash == content_hash)):
            complete_processing_run(
                db,
                processing_run,
                fetched_count=1,
                skipped_duplicate_count=1,
            )
            raise HTTPException(status_code=409, detail="This Screener export has already been uploaded.")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name

        raw_doc = RawDocument(
            company_id=company_id,
            source_id=source.id,
            title=f"Screener.in Export: {filename}",
            url=None,
            document_type="screener_export",
            published_at=datetime.now(timezone.utc),
            raw_text=None,
            raw_payload_json={
                "source_kind": "user_upload",
                "original_filename": filename,
                "reporting_currency": company.currency or "INR",
                "file_size_bytes": len(content),
                "parser": "screener_excel_v1",
                "sha256": digest,
            },
            content_hash=content_hash,
        )
        db.add(raw_doc)
        db.flush()

        candidates = ScreenerExcelParser.parse_screener_excel(
            db=db,
            company_id=company_id,
            raw_document_id=raw_doc.id,
            file_path=temp_path,
            reporting_currency=(company.currency or "INR").upper(),
        )
        db.add_all(candidates)
        db.commit()
        complete_processing_run(
            db,
            processing_run,
            fetched_count=1,
            created_count=len(candidates),
        )
        return ApiResponse(data={"status": "success", "extracted_count": len(candidates)})
    except HTTPException as exc:
        db.rollback()
        if processing_run_id is not None:
            failed_run = db.get(ProcessingRun, processing_run_id)
            if failed_run is not None and failed_run.status == "running":
                fail_processing_run(db, failed_run, error_type="request_error", message=str(exc.detail))
        raise
    except ValueError as exc:
        db.rollback()
        if processing_run_id is not None:
            failed_run = db.get(ProcessingRun, processing_run_id)
            if failed_run is not None:
                fail_processing_run(
                    db,
                    failed_run,
                    error_type="validation_error",
                    message="Workbook validation failed.",
                )
        raise PublicApiError(
            status_code=422,
            code="SCREENER_WORKBOOK_INVALID",
            message="Workbook validation failed. Check required columns, units, and currencies.",
            field="file",
            processing_run_id=processing_run_id,
        ) from exc
    except Exception as exc:
        db.rollback()
        if processing_run_id is not None:
            failed_run = db.get(ProcessingRun, processing_run_id)
            if failed_run is not None:
                fail_processing_run(db, failed_run, error_type=type(exc).__name__)
        raise HTTPException(status_code=500, detail="Unable to process the uploaded workbook.") from exc
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@router.get(
    "/api/companies/{company_id}/financial-statements/extracted",
    response_model=ApiResponse[list[FinancialExtractionCandidateRead]],
)
def list_extracted_financials(company_id: int, db: Session = Depends(get_db)) -> ApiResponse[list[FinancialExtractionCandidateRead]]:
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return ApiResponse(data=list_extracted_financial_candidates(db, company_id))


@router.get(
    "/api/financial-line-items/{candidate_id}",
    response_model=ApiResponse[FinancialExtractionCandidateRead],
)
def get_financial_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse[FinancialExtractionCandidateRead]:
    candidate = db.get(FinancialExtractionCandidate, candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return ApiResponse(data=candidate)


@router.patch(
    "/api/financial-line-items/{candidate_id}/review",
    response_model=ApiResponse[FinancialExtractionCandidateRead],
)
def review_financial_candidate(candidate_id: int, update: schemas.FinancialCandidateReviewUpdate, db: Session = Depends(get_db)):
    return ApiResponse(data=update_candidate_review_status(db, candidate_id, update.review_status))


@router.patch(
    "/api/financial-line-items/{candidate_id}/override",
    response_model=ApiResponse[FinancialExtractionCandidateRead],
)
def override_financial_candidate(candidate_id: int, override: schemas.FinancialCandidateOverride, db: Session = Depends(get_db)):
    return ApiResponse(data=override_candidate_value(db, candidate_id, override.value, override.unit))


@router.post(
    "/api/companies/{company_id}/financial-statements/mark-reviewed",
    response_model=ApiResponse[dict],
)
def promote_financial_candidates(company_id: int, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    promoted_count = promote_reviewed_candidates(db, company_id)
    return ApiResponse(data={"status": "success", "promoted_count": promoted_count})


@router.post("/companies/{company_id}/financial-periods", response_model=ApiResponse[schemas.FinancialStatementPeriodRead], status_code=status.HTTP_201_CREATED)
def create_financial_period(company_id: int, period_in: schemas.FinancialStatementPeriodCreate, db: Session = Depends(get_db)) -> FinancialStatementPeriod:
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    period = FinancialStatementPeriod(**period_in.model_dump())
    period.company_id = company_id
    db.add(period)
    db.commit()
    db.refresh(period)
    return ApiResponse(data=period)


@router.get("/companies/{company_id}/financial-periods", response_model=ApiResponse[list[schemas.FinancialStatementPeriodRead]])
def list_financial_periods(company_id: int, db: Session = Depends(get_db)) -> Sequence[FinancialStatementPeriod]:
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    periods = db.scalars(
        select(FinancialStatementPeriod)
        .where(FinancialStatementPeriod.company_id == company_id)
        .order_by(FinancialStatementPeriod.year.desc(), FinancialStatementPeriod.quarter.desc())
    ).all()
    return ApiResponse(data=periods)


@router.post("/financial-periods/{period_id}/metrics", response_model=ApiResponse[schemas.FinancialMetricRead], status_code=status.HTTP_201_CREATED)
def create_financial_metric(period_id: int, metric_in: schemas.FinancialMetricCreate, db: Session = Depends(get_db)) -> FinancialMetric:
    period = db.get(FinancialStatementPeriod, period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Period not found")

    metric = FinancialMetric(**metric_in.model_dump())
    metric.period_id = period_id
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return ApiResponse(data=metric)


@router.delete("/financial-periods/{period_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_financial_period(period_id: int, db: Session = Depends(get_db)) -> None:
    period = db.get(FinancialStatementPeriod, period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Period not found")

    db.delete(period)
    db.commit()


@router.get("/fundamentals/{ticker}/trends", response_model=ApiResponse[list[FinancialPeriodRead]])
def get_financial_trends(ticker: str, limit: int = 8, db: Session = Depends(get_db)):
    company = db.execute(select(Company).where(Company.ticker == ticker)).scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    periods = db.execute(
        select(FinancialStatementPeriod)
        .where(FinancialStatementPeriod.company_id == company.id)
        .order_by(FinancialStatementPeriod.year.desc(), FinancialStatementPeriod.quarter.desc())
    ).scalars().all()

    return ApiResponse(data=[FinancialPeriodRead.model_validate(p) for p in periods])


@router.post("/fundamentals/ingest/{ticker}", response_model=ApiResponse[dict])
def ingest_fundamentals(ticker: str, db: Session = Depends(get_db)):
    company = db.execute(select(Company).where(Company.ticker == ticker)).scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    return _xbrl_response(db, company.id, legacy=True)

@router.post(
    "/api/companies/{company_id}/financial-statements/{period_id}/normalize",
    response_model=ApiResponse[schemas.NormalizedSnapshotRead],
)
def normalize_financial_period(company_id: int, period_id: int, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    try:
        snapshot = MetricNormalizationEngine.normalize_period(db, period_id)
        return ApiResponse(data=snapshot)
    except ValueError as exc:
        raise PublicApiError(
            status_code=422,
            code="FINANCIAL_NORMALIZATION_FAILED",
            message="The financial period could not be normalized.",
        ) from exc


@router.get(
    "/api/companies/{company_id}/financial-statements/normalized",
    response_model=ApiResponse[list[schemas.NormalizedSnapshotRead]],
)
def list_normalized_snapshots(company_id: int, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    snapshots = db.scalars(
        select(NormalizedFinancialSnapshot)
        .where(NormalizedFinancialSnapshot.company_id == company_id)
    ).all()

    return ApiResponse(data=snapshots)


@router.get(
    "/api/companies/{company_id}/financial-statements/normalized/coverage",
    response_model=ApiResponse[schemas.NormalizedCoverageRead],
)
def get_normalized_snapshot_coverage(company_id: int, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return ApiResponse(data=NormalizedSnapshotBackfillService.summarize(db, company_id))


@router.get(
    "/api/companies/{company_id}/financial-statements/normalized/reconciliation",
    response_model=ApiResponse[schemas.FinancialReconciliationRead],
)
def get_financial_reconciliation(company_id: int, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return ApiResponse(data=FinancialReconciliationService.reconcile(db, company_id))


@router.get(
    "/api/companies/{company_id}/financial-statements/identities",
    response_model=ApiResponse[schemas.FinancialStatementIdentityReportRead],
)
def get_financial_statement_identities(company_id: int, db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return ApiResponse(data=FinancialStatementIdentityService.evaluate_company(db, company_id))


@router.post(
    "/api/companies/{company_id}/financial-statements/normalized/backfill",
    response_model=ApiResponse[schemas.NormalizedBackfillRead],
)
def backfill_normalized_snapshots(
    company_id: int,
    payload: schemas.NormalizedBackfillRequest,
    db: Session = Depends(get_db),
):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    run = start_processing_run(
        db,
        run_type="normalized_financial_backfill",
        source_type="internal",
        company_id=company_id,
        metadata={"dry_run": payload.dry_run},
    )
    try:
        result = NormalizedSnapshotBackfillService.backfill(db, company_id, dry_run=payload.dry_run)
    except Exception as exc:
        db.rollback()
        fail_processing_run(db, run, error_type=type(exc).__name__)
        raise
    complete_processing_run(
        db,
        run,
        fetched_count=result["examined_count"],
        created_count=result["normalized_count"],
        error_count=len(result["skipped_conflicts"]),
        errors=[item["error"] for item in result["skipped_conflicts"]],
        metadata_patch={"eligible_count": result["eligible_count"]},
    )
    return ApiResponse(data=result)
