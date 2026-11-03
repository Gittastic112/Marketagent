"""Audited public-source refresh, shared by queued manual and weekday work.

Each external step commits its own audit. Partial failure never approves facts,
changes saved models, or prevents the remaining providers from being checked.
"""
import asyncio
from dataclasses import asdict
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Company, ProcessingRun
from app.models.user import User
from app.services.daily_brief_schedule import compute_next_scheduled_run
from app.services.macro_ingestion import ingest_fred_series
from app.services.market_data.ingestion import ingest_company_prices
from app.services.processing_runs import start_processing_run, complete_processing_run, fail_processing_run
from app.services.sec_xbrl_extractor import company_sec_cik, extract_xbrl_candidates
from app.services.valuation_setup_draft import ValuationSetupDraftService

RUN_TYPE = "valuation_source_refresh"
ZONE = "America/New_York"
LOCAL_TIME = time(7, 0)
WEEKDAYS = [0, 1, 2, 3, 4]
LOCK_ID = 736218042


def _owned_runs(user_id: str):
    return select(ProcessingRun).where(ProcessingRun.run_type == RUN_TYPE,
        ProcessingRun.metadata_json["user_id"].as_string() == user_id)


def run_response(run: ProcessingRun) -> dict:
    metadata = run.metadata_json or {}
    return {"id": run.id, "company_id": run.company_id, "status": run.status,
        "started_at": run.started_at, "finished_at": run.finished_at,
        "scheduled_for": metadata.get("scheduled_for"), "steps": metadata.get("steps", []),
        "warnings": metadata.get("warnings", []), "draft_ids": metadata.get("draft_ids", [])}


def refresh_status(db: Session, user_id: str, company_id: int | None = None, now=None) -> dict:
    now = now or datetime.now(UTC)
    settings = get_settings()
    enabled = settings.valuation_refresh_enabled and user_id == settings.valuation_refresh_owner_id
    query = _owned_runs(user_id)
    if company_id is not None:
        query = query.where((ProcessingRun.company_id == company_id) | ProcessingRun.company_id.is_(None))
    latest = db.scalar(query.order_by(ProcessingRun.id.desc()).limit(1))
    next_run = compute_next_scheduled_run(timezone_name=ZONE, local_time=LOCAL_TIME,
        days_of_week=WEEKDAYS, after_utc=now) if enabled else None
    return {"enabled": enabled, "timezone": ZONE, "local_time": "07:00", "weekdays": WEEKDAYS,
        "next_scheduled_at": next_run, "latest_run": run_response(latest) if latest else None,
        "policy": "Latest completed annual financials; draft suggestions only; saved models and review decisions unchanged.",
        "runtime_requirement": "Computer, Docker and the source-refresh worker must be running. Missed weekdays are not backfilled."}


def enqueue_company_refresh(db: Session, company_id: int, user_id: str) -> ProcessingRun:
    company = db.scalar(select(Company).where(Company.id == company_id).with_for_update())
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    existing = db.scalar(_owned_runs(user_id).where(ProcessingRun.company_id == company_id,
        ProcessingRun.status.in_(["queued", "running"])).order_by(ProcessingRun.id.desc()).limit(1))
    if existing:
        db.commit()
        return existing
    run = ProcessingRun(run_type=RUN_TYPE, source_type="public_sources", company_id=company_id,
        started_at=datetime.now(UTC), status="queued", metadata_json={"user_id": user_id, "steps": []})
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def cancel_queued_refresh(db: Session, run_id: int, user_id: str) -> ProcessingRun:
    """Cancel an owned queue entry while excluding the source worker's claim path."""
    run = db.scalar(_owned_runs(user_id).where(ProcessingRun.id == run_id))
    if run is None:
        raise HTTPException(status_code=404, detail="Source refresh not found")
    connection, acquired = None, False
    try:
        engine = db.get_bind()
        if engine.dialect.name == "postgresql":
            connection = engine.connect()
            acquired = bool(connection.scalar(text("SELECT pg_try_advisory_lock(:key)"), {"key": LOCK_ID}))
            if not acquired:
                raise HTTPException(status_code=409, detail="The source-refresh worker is busy. Wait for it to finish before cancelling.")
        db.refresh(run, with_for_update=True)
        if run.status == "cancelled":
            return run
        if run.status != "queued":
            raise HTTPException(status_code=409, detail="Only a queued source refresh can be cancelled. Reload to check its current status.")
        run.status = "cancelled"
        run.finished_at = datetime.now(UTC)
        run.metadata_json = {**(run.metadata_json or {}), "cancelled_by": user_id,
            "warnings": [*((run.metadata_json or {}).get("warnings") or []),
                "Cancelled before source processing. Existing source data and saved models were preserved."]}
        db.commit()
        db.refresh(run)
        return run
    finally:
        if connection is not None:
            if acquired:
                connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": LOCK_ID})
            connection.close()


def _source_step(db, parent, name, callback, *, run_type, company_id=None, metadata=None):
    child = start_processing_run(db, run_type=run_type, source_type="macro" if name.startswith("FRED") else "sec",
        company_id=company_id, metadata={"parent_run_id": parent.id, **(metadata or {})})
    try:
        result = callback()
        if not isinstance(result, dict):
            result = asdict(result)
        errors = list(result.get("errors", []))
        complete_processing_run(db, child, fetched_count=result.get("fetched_count", 0),
            created_count=result.get("created_count", 0),
            skipped_duplicate_count=result.get("skipped_duplicate_count", result.get("skipped_existing_count", 0)),
            error_count=result.get("error_count", 0), errors=errors,
            metadata_patch={key: value for key, value in result.items() if key not in {"errors"}})
        return {"name": name, "company_id": company_id, "status": child.status, "run_id": child.id,
            "created_count": child.created_count, "warnings": result.get("warnings", []) + errors}
    except Exception:
        db.rollback()
        fail_processing_run(db, child, error_type="source_refresh_failed",
            message="Source refresh failed. Check provider configuration and Processing Runs.")
        return {"name": name, "company_id": company_id, "status": "failed", "run_id": child.id,
            "warnings": [f"{name} refresh failed; stored evidence was not replaced by a successful live response."]}


def execute_refresh(db: Session, run: ProcessingRun) -> ProcessingRun:
    settings = get_settings()
    owner = (run.metadata_json or {})["user_id"]
    run.status = "running"
    run.started_at = datetime.now(UTC)
    db.commit()
    steps, draft_ids = [], []

    def progress(step):
        steps.append(step)
        run.metadata_json = {**run.metadata_json, "steps": list(steps), "draft_ids": list(draft_ids)}
        db.commit()

    for series in ("DGS10", "NFCI"):
        if not settings.fred_api_key:
            progress({"name": f"FRED {series}", "status": "not_configured", "warnings": ["FRED key is not configured."]})
            continue
        progress(_source_step(db, run, f"FRED {series}",
            lambda: ingest_fred_series(db, series, api_key=settings.fred_api_key),
            run_type="fred_ingestion", metadata={"series_id": series}))
    query = select(Company).where(Company.id == run.company_id) if run.company_id else select(Company).where(
        Company.active.is_(True), Company.primary_exchange.is_not(None), Company.local_symbol.is_not(None))
    company_ids = list(db.scalars(query.with_only_columns(Company.id).order_by(Company.id)))
    for company_id in company_ids:
        company = db.get(Company, company_id)
        if company_sec_cik(company):
            progress(_source_step(db, run, "SEC annual facts", lambda: extract_xbrl_candidates(db, company_id),
                run_type="sec_xbrl_extraction", company_id=company_id, metadata={"provider": "SEC companyfacts"}))
        else:
            progress({"name": "SEC annual facts", "company_id": company_id, "status": "not_available",
                "warnings": ["No supported SEC issuer identity. Upload and review annual statements for this company."]})
        try:
            result = asyncio.run(ingest_company_prices(db, company=company, user_id=owner, days=7, parent_run_id=run.id))
            progress({"name": "Prices", "company_id": company_id, "status": "success",
                "run_id": result.processing_run_id, "created_count": result.created_count, "warnings": []})
        except Exception as exc:
            db.rollback()
            progress({"name": "Prices", "company_id": company_id, "status": "failed",
                "run_id": getattr(exc, "processing_run_id", None),
                "warnings": ["Price refresh failed. Any stored price retains its original date and freshness warning."]})
        try:
            draft = ValuationSetupDraftService.create_or_reopen(db, company_id, owner)
            draft = ValuationSetupDraftService.refresh(db, draft)
            draft_ids.append(draft.id)
            progress({"name": "Draft", "company_id": company_id, "status": "success", "draft_id": draft.id,
                "warnings": ["Review required. Saved models and financial review decisions were not changed."]})
        except Exception:
            db.rollback()
            progress({"name": "Draft", "company_id": company_id, "status": "failed",
                "warnings": ["Draft could not be refreshed. Existing saved models remain unchanged."]})
    warnings = [message for step in steps for message in step.get("warnings", [])]
    failures = sum(step["status"] in {"failed", "not_configured", "not_available", "partial_success"} for step in steps)
    return complete_processing_run(db, run, fetched_count=len(company_ids), created_count=len(draft_ids),
        error_count=failures, errors=["Some source steps remain incomplete."] if failures else [],
        metadata_patch={"steps": steps, "draft_ids": draft_ids, "warnings": list(dict.fromkeys(warnings))})


def run_refresh_cycle(db: Session, *, now: datetime | None = None) -> dict:
    """Single local worker. PostgreSQL lock survives step commits and prevents replicas racing."""
    now = now or datetime.now(UTC)
    settings = get_settings()
    engine = db.get_bind()
    lock_connection = None
    if engine.dialect.name == "postgresql":
        lock_connection = engine.connect()
        if not lock_connection.scalar(text("SELECT pg_try_advisory_lock(:key)"), {"key": LOCK_ID}):
            lock_connection.close()
            return {"processed": 0, "locked": True}
    try:
        # Under the exclusive worker lock, a previously running job means its
        # worker exited. Mark it failed explicitly; do not retry providers blindly.
        interrupted = db.scalars(select(ProcessingRun).where(ProcessingRun.run_type == RUN_TYPE,
            ProcessingRun.status == "running")).all()
        for run in interrupted:
            children = db.scalars(select(ProcessingRun).where(ProcessingRun.status == "running",
                ProcessingRun.metadata_json["parent_run_id"].as_integer() == run.id)).all()
            for child in children:
                fail_processing_run(db, child, error_type="worker_interrupted",
                    message="Source worker stopped before this attempt completed; retry explicitly.")
            fail_processing_run(db, run, error_type="worker_interrupted", message="Refresh worker stopped before completion; retry explicitly.")
        local = now.astimezone(ZoneInfo(ZONE))
        if settings.valuation_refresh_enabled and local.weekday() in WEEKDAYS and local.time() >= LOCAL_TIME:
            day_key = local.date().isoformat()
            owner = settings.valuation_refresh_owner_id
            existing = db.scalar(_owned_runs(owner).where(ProcessingRun.metadata_json["scheduled_for"].as_string() == day_key).limit(1))
            if existing is None and db.get(User, owner) is not None:
                db.add(ProcessingRun(run_type=RUN_TYPE, source_type="public_sources", started_at=now,
                    status="queued", metadata_json={"user_id": owner, "scheduled_for": day_key, "steps": []}))
                db.commit()
        queued = db.scalars(select(ProcessingRun).where(ProcessingRun.run_type == RUN_TYPE,
            ProcessingRun.status == "queued").order_by(ProcessingRun.id).limit(5)).all()
        for run in queued:
            try:
                execute_refresh(db, run)
            except Exception:
                db.rollback()
                fail_processing_run(db, run, error_type="refresh_failed", message="Refresh did not complete. Review Processing Runs before retrying.")
        return {"processed": len(queued), "locked": False}
    finally:
        if lock_connection is not None:
            lock_connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": LOCK_ID})
            lock_connection.close()
