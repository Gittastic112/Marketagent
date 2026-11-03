"""Audited candidate-only SEC workflow shared by current and legacy HTTP routes."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.services.processing_runs import complete_processing_run, fail_processing_run, start_processing_run
from app.services.sec_xbrl_extractor import extract_xbrl_candidates


class XbrlIngestionError(Exception):
    def __init__(self, processing_run_id: int):
        super().__init__("SEC company facts ingestion failed.")
        self.processing_run_id = processing_run_id


def ingest_xbrl_candidates(db: Session, company_id: int, *, run_type="sec_xbrl_extraction") -> dict:
    run = start_processing_run(db, run_type=run_type, source_type="sec", company_id=company_id,
        metadata={"provider": "SEC companyfacts", "review_required": True})
    try:
        result = extract_xbrl_candidates(db, company_id)
    except HTTPException as exc:
        db.rollback()
        fail_processing_run(db, run, error_type="request_error", message=str(exc.detail))
        raise
    except Exception as exc:
        db.rollback()
        fail_processing_run(db, run, error_type=type(exc).__name__)
        raise XbrlIngestionError(run.id) from None
    complete_processing_run(db, run, fetched_count=result.get("fetched_count", 0),
        created_count=result.get("created_count", 0),
        skipped_duplicate_count=result.get("skipped_existing_count", 0),
        metadata_patch={key: result.get(key, [] if key != "missing_core_metrics_by_year" else {})
            for key in ("warnings", "selected_fiscal_years", "missing_core_metrics_by_year")})
    return result
