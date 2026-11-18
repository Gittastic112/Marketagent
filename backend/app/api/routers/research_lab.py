"""Authenticated research operations; every calculation has an owned receipt."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.errors import PublicApiError
from app.db.session import get_db
from app.schemas.common import ApiMeta, ApiResponse
from app.schemas.research_lab import (
    AllocationRequest,
    PeerDiscoveryRequest,
    ReportRequest,
    ResearchCapabilities,
    ResearchRunResult,
    ResearchRunSummary,
    SimulationRequest,
)
from app.services.research_lab import service
from app.services.research_lab.common import canonical_json
from app.services.research_lab.errors import ResearchAdapterError
from app.services.research_lab.reporting import render_html


router = APIRouter(prefix="/api/research-lab", tags=["research-lab"])


def _public(exc: ResearchAdapterError) -> PublicApiError:
    return PublicApiError(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
        processing_run_id=getattr(exc, "processing_run_id", None),
        retryable=exc.code in {"RESEARCH_WORKER_BUSY", "RESEARCH_TIMEOUT"},
    )


def _execute(
    db: Session, user: dict, kind: service.Kind, payload
) -> ApiResponse[ResearchRunResult]:
    try:
        result = service.execute(db, str(user["id"]), kind, payload)
    except ResearchAdapterError as exc:
        raise _public(exc) from exc
    return ApiResponse(
        data=result,
        meta=ApiMeta(
            source=result.manifest.adapter,
            warnings=result.warnings,
            last_updated=result.manifest.created_at,
            confidence="low",
        ),
    )


@router.get("/capabilities", response_model=ApiResponse[ResearchCapabilities])
def research_capabilities() -> ApiResponse[ResearchCapabilities]:
    return ApiResponse(data=service.capabilities())


@router.post("/allocation", response_model=ApiResponse[ResearchRunResult])
def allocation(
    payload: AllocationRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return _execute(db, user, "allocation", payload)


@router.post("/simulation", response_model=ApiResponse[ResearchRunResult])
def simulation(
    payload: SimulationRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return _execute(db, user, "simulation", payload)


@router.post("/report", response_model=ApiResponse[ResearchRunResult])
def report(
    payload: ReportRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return _execute(db, user, "report", payload)


@router.post("/peers", response_model=ApiResponse[ResearchRunResult])
def peers(
    payload: PeerDiscoveryRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return _execute(db, user, "peers", payload)


@router.get("/runs", response_model=ApiResponse[list[ResearchRunSummary]])
def runs(
    limit: int = Query(default=25, ge=1, le=100),
    before_run_id: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    return ApiResponse(data=service.history(db, str(user["id"]), limit, before_run_id))


@router.get("/runs/{run_id}", response_model=ApiResponse[ResearchRunResult])
def run(
    run_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)
):
    try:
        saved = service.saved_run(db, str(user["id"]), run_id)
    except ResearchAdapterError as exc:
        raise _public(exc) from exc
    return ApiResponse(
        data=ResearchRunResult.model_validate(
            {key: value for key, value in saved.items() if key != "input"}
        )
    )


@router.get("/runs/{run_id}/export", response_class=Response)
def export(
    run_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)
):
    try:
        saved = service.saved_run(db, str(user["id"]), run_id)
    except ResearchAdapterError as exc:
        raise _public(exc) from exc
    return Response(
        canonical_json(saved),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="marketagent-research-{run_id}.json"',
            "Cache-Control": "private, no-store",
        },
    )


@router.get("/runs/{run_id}/report.html", response_class=Response)
def html_report(
    run_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)
):
    try:
        saved = service.saved_run(db, str(user["id"]), run_id)
    except ResearchAdapterError as exc:
        raise _public(exc) from exc
    return Response(
        render_html(saved),
        media_type="text/html",
        headers={
            "Content-Disposition": f'attachment; filename="marketagent-research-{run_id}.html"',
            "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; sandbox",
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store",
        },
    )
