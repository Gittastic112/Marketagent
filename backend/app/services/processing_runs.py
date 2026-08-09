from datetime import UTC, datetime
import logging
from typing import Any, Protocol

from sqlalchemy.orm import Session

from app.models import ProcessingRun


logger = logging.getLogger(__name__)


class IngestionResult(Protocol):
    fetched_count: int
    created_count: int
    skipped_duplicate_count: int
    error_count: int
    errors: tuple[str, ...]


def start_processing_run(
    db: Session,
    *,
    run_type: str,
    source_type: str | None = None,
    source_id: int | None = None,
    company_id: int | None = None,
    fetched_count: int = 0,
    metadata: dict[str, Any] | None = None,
) -> ProcessingRun:
    run = ProcessingRun(
        run_type=run_type,
        source_type=source_type,
        source_id=source_id,
        company_id=company_id,
        started_at=datetime.now(UTC),
        status="running",
        fetched_count=fetched_count,
        metadata_json=metadata,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    logger.info(
        "Processing run started",
        extra={
            "processing_run_id": run.id,
            "run_type": run.run_type,
            "company_id": run.company_id,
        },
    )
    return run


def complete_processing_run(
    db: Session,
    run: ProcessingRun,
    *,
    fetched_count: int | None = None,
    created_count: int = 0,
    skipped_duplicate_count: int = 0,
    error_count: int = 0,
    errors: list[str] | tuple[str, ...] | None = None,
    metadata_patch: dict[str, Any] | None = None,
) -> ProcessingRun:
    persisted = db.get(ProcessingRun, run.id)
    if persisted is None:
        raise ValueError(f"Processing run {run.id} not found")
    if fetched_count is not None:
        persisted.fetched_count = fetched_count
    persisted.created_count = created_count
    persisted.skipped_duplicate_count = skipped_duplicate_count
    persisted.error_count = error_count
    persisted.error_details_json = {"errors": list(errors)} if errors else None
    persisted.metadata_json = {**(persisted.metadata_json or {}), **(metadata_patch or {})} or None
    persisted.status = _status_for_counts(error_count=error_count, created_count=created_count)
    persisted.finished_at = datetime.now(UTC)
    db.commit()
    db.refresh(persisted)
    logger.info(
        "Processing run completed",
        extra={
            "processing_run_id": persisted.id,
            "run_type": persisted.run_type,
            "run_status": persisted.status,
            "error_count": persisted.error_count,
        },
    )
    return persisted


def fail_processing_run(
    db: Session,
    run: ProcessingRun,
    *,
    error_type: str,
    message: str | None = None,
) -> ProcessingRun:
    persisted = db.get(ProcessingRun, run.id)
    if persisted is None:
        raise ValueError(f"Processing run {run.id} not found")
    persisted.status = "failed"
    persisted.error_count = 1
    persisted.error_details_json = {
        "error_type": error_type,
        **({"message": message} if message else {}),
    }
    persisted.finished_at = datetime.now(UTC)
    db.commit()
    db.refresh(persisted)
    logger.warning(
        "Processing run failed",
        extra={
            "processing_run_id": persisted.id,
            "run_type": persisted.run_type,
            "run_status": persisted.status,
            "error_type": error_type,
        },
    )
    return persisted


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
    logger.info(
        "Processing run recorded",
        extra={
            "processing_run_id": run.id,
            "run_type": run.run_type,
            "run_status": run.status,
            "error_count": run.error_count,
        },
    )
    return run


def _status_for_result(result: IngestionResult) -> str:
    return _status_for_counts(error_count=result.error_count, created_count=result.created_count)


def _status_for_counts(*, error_count: int, created_count: int) -> str:
    if error_count == 0:
        return "success"
    if created_count > 0:
        return "partial_success"
    return "failed"
