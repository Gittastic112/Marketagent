from datetime import UTC, datetime
from time import perf_counter

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.schemas import ApiMeta, ApiResponse, EvidenceSearchResultRead, SearchResultType
from app.db.session import get_db
from app.services.evidence_search import search_evidence


router = APIRouter()
SEARCH_QUERY_BUDGET = 14
SEARCH_RESPONSE_BUDGET_MS = 750


def normalize_search_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


@router.get("/search/evidence", response_model=ApiResponse[list[EvidenceSearchResultRead]])
def search_stored_evidence(
    q: str = Query(min_length=2, max_length=200),
    company_id: int | None = None,
    result_type: SearchResultType | None = Query(default=None, alias="type"),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[list[dict]]:
    started_at = perf_counter()
    results = search_evidence(
        db,
        q,
        user_id=current_user["id"],
        company_id=company_id,
        result_type=result_type,
        limit=limit,
    )
    processing_time_ms = round((perf_counter() - started_at) * 1_000)
    warnings = []
    if processing_time_ms > SEARCH_RESPONSE_BUDGET_MS:
        warnings.append(f"Corpus search exceeded the {SEARCH_RESPONSE_BUDGET_MS} ms local budget.")
    timestamps = [
        normalize_search_timestamp(item["source_timestamp"])
        for item in results
        if item["source_timestamp"]
    ]
    return ApiResponse(
        data=results,
        meta=ApiMeta(
            source="stored_corpus",
            last_updated=max(timestamps) if timestamps else None,
            is_mock=any(item.get("is_mock", False) for item in results),
            confidence="medium",
            processing_time_ms=processing_time_ms,
            warnings=warnings,
        ),
    )
