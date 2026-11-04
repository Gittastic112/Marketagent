import logging
from datetime import UTC, datetime
from time import perf_counter

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, noload, selectinload

from app.api.dependencies import get_current_user
from app.api.schemas import ApiMeta, ApiResponse, DashboardOverviewRead
from app.db.session import get_db
from app.models import (
    Alert,
    Company,
    Event,
    Portfolio,
    PortfolioSnapshot,
    ProcessingRun,
    RawDocument,
    Source,
    ThesisAssumption,
    ThesisNote,
)
from app.services.morning_briefing_engine import MorningBriefingEngine
from app.services.brief_public_coverage import count_public_inputs, is_failed_run, public_coverage_context


router = APIRouter()
logger = logging.getLogger(__name__)
DASHBOARD_QUERY_BUDGET = 20
DASHBOARD_RESPONSE_BUDGET_MS = 1_000


@router.get("/dashboard/overview", response_model=ApiResponse[DashboardOverviewRead])
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[dict]:
    started_at = perf_counter()
    captured_at = datetime.now(UTC)
    user_id = current_user["id"]
    companies = list(
        db.scalars(
            select(Company)
            .options(noload("*"), selectinload(Company.exposure_tags).options(noload("*")))
            .order_by(Company.id)
        )
    )
    events = list(
        db.scalars(
            select(Event)
            .options(
                noload("*"),
                selectinload(Event.company).options(noload("*")),
                selectinload(Event.corroborates).options(noload("*")),
                selectinload(Event.contradicts).options(noload("*")),
                joinedload(Event.raw_document).load_only(
                    RawDocument.id, RawDocument.source_id, RawDocument.url, RawDocument.published_at,
                ).options(noload("*"), joinedload(RawDocument.source).load_only(Source.id, Source.name).options(noload("*"))),
            )
            .where(Event.created_at <= captured_at)
            .order_by(Event.priority_score.desc().nullslast(), Event.created_at.desc())
            .limit(50)
        )
    )
    alerts = list(
        db.scalars(
            select(Alert)
            .options(
                noload("*"),
                selectinload(Alert.portfolio_impacts).options(noload("*")),
            )
            .where(Alert.user_id == user_id)
            .order_by(Alert.created_at.desc(), Alert.id.desc())
            .limit(100)
        )
    )
    thesis_notes = list(
        db.scalars(
            select(ThesisNote)
            .options(
                noload("*"),
                selectinload(ThesisNote.assumptions).options(
                    noload("*"),
                    selectinload(ThesisAssumption.impacts).options(noload("*")),
                ),
                selectinload(ThesisNote.changes).options(noload("*")),
            )
            .where(ThesisNote.user_id == user_id)
            .order_by(ThesisNote.id)
        )
    )
    processing_runs = list(
        db.scalars(
            select(ProcessingRun)
            .options(noload("*"))
            .where(ProcessingRun.started_at <= captured_at)
            .order_by(ProcessingRun.created_at.desc(), ProcessingRun.id.desc())
            .limit(20)
        )
    )
    portfolio = db.scalar(
        select(Portfolio)
        .options(noload("*"))
        .where(Portfolio.user_id == user_id)
        .order_by(Portfolio.id)
        .limit(1)
    )
    portfolio_snapshot = None
    warnings: list[str] = []
    if portfolio is not None:
        portfolio_snapshot = db.scalar(
            select(PortfolioSnapshot)
            .options(noload("*"))
            .where(PortfolioSnapshot.portfolio_id == portfolio.id)
            .order_by(PortfolioSnapshot.snapshot_date.desc(), PortfolioSnapshot.id.desc())
            .limit(1)
        )
        if portfolio_snapshot is not None and portfolio_snapshot.calculation_status != "complete":
            warnings.append(
                "The latest portfolio snapshot is partial; missing prices or FX remain unavailable."
            )

    preview_events = events[:10]
    preview_failures = [run for run in processing_runs if is_failed_run(run)][:10]
    event_total, failed_run_total = count_public_inputs(db, None, captured_at)
    coverage = public_coverage_context(captured_at=captured_at, start=None, end=captured_at,
        basis="dashboard_preview", event_total=event_total, event_included=len(preview_events), event_cap=10,
        failed_run_total=failed_run_total, failed_run_included=len(preview_failures), failed_run_cap=10,
        failed_run_reason="dashboard_recent_run_preview")
    daily_brief = MorningBriefingEngine.build_briefing_payload(
        db, user_id, preview_events, thesis_notes, allow_generation=False,
        include_portfolio_moves=False, persisted_alerts=alerts,
        processing_failures=preview_failures, public_coverage=coverage,
    )
    processing_time_ms = round((perf_counter() - started_at) * 1_000)
    if processing_time_ms > DASHBOARD_RESPONSE_BUDGET_MS:
        logger.warning(
            "Dashboard overview took %s ms, above the %s ms local budget.",
            processing_time_ms,
            DASHBOARD_RESPONSE_BUDGET_MS,
        )

    return ApiResponse(
        data={
            "companies": companies,
            "events": events,
            "alerts": alerts,
            "thesis_notes": thesis_notes,
            "daily_brief": daily_brief,
            "processing_runs": processing_runs,
            "default_portfolio": portfolio,
            "default_portfolio_snapshot": portfolio_snapshot,
            "portfolio_analytics": None,
        },
        meta=ApiMeta(
            source="internal",
            warnings=warnings,
            processing_time_ms=processing_time_ms,
        ),
    )
