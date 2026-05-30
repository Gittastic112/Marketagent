from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy.orm import Session

from app.models import ProcessingRun


class IngestionResult(Protocol):
    fetched_count: int
    created_count: int
    skipped_duplicate_count: int
    error_count: int
    errors: tuple[str, ...]


def record_ingestion_run(
    db: Session,
    *,
    run_type: str,
    source_type: str | None,
    source_id: int | None,
    company_id: int | None,
    result: IngestionResult,
    started_at: datetime | None = None,
    metadata: dict | None = None,
) -> ProcessingRun:
    finished_at = datetime.now(UTC)
    run = ProcessingRun(
        run_type=run_type,
        source_type=source_type,
        source_id=source_id,
        company_id=company_id,
        started_at=started_at or finished_at,
        finished_at=finished_at,
        status=_status_for_result(result),
        fetched_count=result.fetched_count,
        created_count=result.created_count,
        skipped_duplicate_count=result.skipped_duplicate_count,
        error_count=result.error_count,
        error_details_json={"errors": list(result.errors)} if result.errors else None,
        metadata_json=metadata,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def _status_for_result(result: IngestionResult) -> str:
    if result.error_count == 0:
        return "success"
    if result.created_count > 0:
        return "partial_success"
    return "failed"
