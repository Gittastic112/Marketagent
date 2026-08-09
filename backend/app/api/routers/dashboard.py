from time import perf_counter

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, noload, selectinload

from app.api.dependencies import get_current_user
from app.api.schemas import ApiMeta, ApiResponse, DashboardOverviewRead
from app.db.session import get_db
from app.models import (
    Alert,
    Company,
    Event,
    Portfolio,
    ProcessingRun,
    RawDocument,
    ThesisAssumption,
    ThesisNote,
)
from app.services.morning_briefing_engine import MorningBriefingEngine
from app.services.portfolio_analytics import calculate_portfolio_analytics


router = APIRouter()
DASHBOARD_QUERY_BUDGET = 20
DASHBOARD_RESPONSE_BUDGET_MS = 1_000


@router.get("/dashboard/overview", response_model=ApiResponse[DashboardOverviewRead])
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[dict]:
    started_at = perf_counter()
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
                selectinload(Event.raw_document).options(
                    noload("*"),
                    selectinload(RawDocument.source).options(noload("*")),
                ),
                selectinload(Event.corroborates).options(noload("*")),
                selectinload(Event.contradicts).options(noload("*")),
            )
            .order_by(Event.priority_score.desc().nullslast(), Event.created_at.desc())
            .limit(50)
        )
    )
    alerts = list(
        db.scalars(
            select(Alert)
            .options(
                noload("*"),
                selectinload(Alert.company).options(noload("*")),
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
    analytics = None
    warnings: list[str] = []
    if portfolio is not None:
        try:
            analytics = calculate_portfolio_analytics(
                db,
                portfolio.id,
                user_id=user_id,
            )
            if analytics["total_invested_value"] is None and analytics["top_positions"]:
                warnings.append("Default portfolio analytics are partial until every holding has a dated market price.")
        except ValueError:
            warnings.append("Default portfolio analytics are unavailable until holdings have dated market prices.")

    processing_time_ms = round((perf_counter() - started_at) * 1_000)
    if processing_time_ms > DASHBOARD_RESPONSE_BUDGET_MS:
        warnings.append(
            f"Dashboard generation exceeded the {DASHBOARD_RESPONSE_BUDGET_MS} ms local budget."
        )

    return ApiResponse(
        data={
            "companies": companies,
            "events": events,
            "alerts": alerts,
            "thesis_notes": thesis_notes,
            "daily_brief": MorningBriefingEngine.build_briefing_payload(db, user_id, events[:10], thesis_notes),
            "processing_runs": processing_runs,
            "default_portfolio": portfolio,
            "portfolio_analytics": analytics,
        },
        meta=ApiMeta(
            source="internal",
            warnings=warnings,
            processing_time_ms=processing_time_ms,
        ),
    )
