from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.schemas import (
    ApiMeta,
    ApiResponse,
    DamodaranCoverageReportRead,
    EventEvidenceBackfillReportRead,
    EventEvidenceBackfillRequest,
    EvidenceIntegrityReportRead,
    PeerReviewReceiptHealthRead,
)
from app.db.session import get_db
from app.services.evidence_integrity import (
    build_evidence_integrity_report,
    build_peer_review_receipt_health,
)
from app.services.damodaran_coverage import build_damodaran_coverage_report
from app.services.event_evidence_backfill import (
    execute_event_evidence_backfill,
    preview_event_evidence_backfill,
)


router = APIRouter(prefix="/data-health", tags=["data-health"])


@router.get(
    "/peer-review-receipts",
    response_model=ApiResponse[PeerReviewReceiptHealthRead],
)
def get_peer_review_receipt_health(
    limit: int = Query(default=50, ge=1, le=100),
    after_id: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[dict]:
    report = build_peer_review_receipt_health(db, user_id=current_user["id"], limit=limit, after_id=after_id)
    attention_count = report["missing_receipt_count"] + report["stale_receipt_count"]
    warnings = (
        [f"{attention_count} active reviewed peer set(s) need diagnostic re-acknowledgement."]
        if attention_count
        else []
    )
    if report["storage_blocked_count"]:
        warnings.append(f'{report["storage_blocked_count"]} reviewed set(s) on this page have conflicting stored evidence.')
    if report["coverage_blocked_count"]:
        warnings.append(f'{report["coverage_blocked_count"]} reviewed set(s) on this page have no usable multiple method.')
    if report["has_more"]:
        warnings.append("Additional owned peer sets remain unchecked; continue to the next audit page.")
    return ApiResponse(
        data=report,
        meta=ApiMeta(
            source="owned_peer_review_receipt_audit",
            last_updated=report["generated_at"],
            confidence="high",
            warnings=warnings,
        ),
    )


@router.get(
    "/damodaran-coverage",
    response_model=ApiResponse[DamodaranCoverageReportRead],
)
def get_damodaran_coverage(db: Session = Depends(get_db)) -> ApiResponse[dict]:
    report = build_damodaran_coverage_report(db)
    return ApiResponse(
        data=report,
        meta=ApiMeta(
            source="damodaran_application_coverage",
            last_updated=report["generated_at"],
            confidence="high",
            warnings=report["warnings"],
        ),
    )


@router.get("/evidence-integrity", response_model=ApiResponse[EvidenceIntegrityReportRead])
def get_evidence_integrity(
    deep: bool = True,
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    report = build_evidence_integrity_report(db, deep_asset_validation=deep)
    warnings = list(report["limitations"])
    if report["error_count"]:
        warnings.append(f'Evidence integrity found {report["error_count"]} blocking error(s).')
    if report["is_truncated"]:
        warnings.append("Evidence integrity issue output was truncated; resolve reported errors and run it again.")
    return ApiResponse(
        data=report,
        meta=ApiMeta(
            source="internal_evidence_audit",
            last_updated=report["checked_at"],
            confidence="high",
            warnings=warnings,
        ),
    )


@router.get(
    "/event-evidence-backfill",
    response_model=ApiResponse[EventEvidenceBackfillReportRead],
)
def get_event_evidence_backfill_preview(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[dict]:
    if limit < 1 or limit > 200:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 200")
    report = preview_event_evidence_backfill(db, user_id=current_user["id"], limit=limit)
    return ApiResponse(
        data=report,
        meta=ApiMeta(
            source="stored_event_evidence_preview",
            last_updated=report["generated_at"],
            confidence="high",
            warnings=report["limitations"],
        ),
    )


@router.post(
    "/event-evidence-backfill",
    response_model=ApiResponse[EventEvidenceBackfillReportRead],
)
def run_event_evidence_backfill(
    payload: EventEvidenceBackfillRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[dict]:
    try:
        report = execute_event_evidence_backfill(
            db,
            user_id=current_user["id"],
            dry_run=payload.dry_run,
            limit=payload.limit,
            event_ids=payload.event_ids,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Event evidence backfill failed; inspect the recorded processing run.",
        ) from exc
    return ApiResponse(
        data=report,
        meta=ApiMeta(
            source="deterministic_event_evidence_backfill",
            last_updated=report["generated_at"],
            confidence="high",
            warnings=report["limitations"],
        ),
    )
