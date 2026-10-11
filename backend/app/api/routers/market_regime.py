from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.errors import PublicApiError
from app.db.session import get_db
from app.services.market_regime_engine import MarketRegimeEngine
from app.api.dependencies import get_current_user
from app.api.schemas import (
    ApiMeta,
    ApiResponse,
    MarketRegimeInputCreate,
    MarketRegimeInputRead,
    MarketRegimeMacroProviderRead,
    MarketRegimeScoreRead,
)
from app.models.market_regime_input import MarketRegimeInput
from app.services.market_regime_macro_provider import (
    apply_nfci_macro_input,
    preview_nfci_macro_input,
)

router = APIRouter(prefix="/market-regime", tags=["market-regime"])

@router.get("/current", response_model=ApiResponse[MarketRegimeScoreRead])
def get_current_regime(
    db: Session = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    """Returns the most recent or newly calculated market regime score."""
    engine = MarketRegimeEngine(db)
    score = engine.get_current_regime()
    return ApiResponse(
        data=score,
        meta=ApiMeta(
            source="market_regime_inputs",
            last_updated=score.created_at,
            is_stale=score.calculation_status == "stale",
            warnings=score.warnings,
            confidence=score.confidence,
        ),
    )

@router.post("/inputs", response_model=ApiResponse[MarketRegimeInputRead])
def submit_market_regime_input(
    payload: MarketRegimeInputCreate,
    db: Session = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
):
    """Submit a manual or automated market regime metric input."""
    db_input = MarketRegimeInput(
        metric_name=payload.metric_name,
        value=payload.value,
        as_of_date=payload.as_of_date,
        source_url=str(payload.source_url) if payload.source_url is not None else None,
        source_name=payload.source_name,
        input_type=payload.input_type,
        methodology=payload.methodology,
    )
    db.add(db_input)
    db.commit()
    db.refresh(db_input)
    MarketRegimeEngine(db).calculate_regime_score()
    return ApiResponse(
        data=db_input,
        meta=ApiMeta(
            source="manual" if db_input.input_type == "manual" else "declared_provider_input",
            last_updated=db_input.created_at,
            confidence="medium",
        ),
    )


@router.get(
    "/providers/fred/macro/preview",
    response_model=ApiResponse[MarketRegimeMacroProviderRead],
)
def preview_fred_macro_regime_input(
    db: Session = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
) -> ApiResponse[dict]:
    preview = preview_nfci_macro_input(db)
    return ApiResponse(
        data=preview,
        meta=ApiMeta(
            source="FRED",
            last_updated=None,
            is_stale=preview["is_stale"],
            warnings=[*preview["warnings"], *preview["blockers"]],
            confidence=(
                "none"
                if preview["blockers"]
                else "low"
                if preview["is_stale"]
                else "high"
            ),
        ),
    )


@router.post(
    "/providers/fred/macro/apply",
    response_model=ApiResponse[MarketRegimeMacroProviderRead],
)
def apply_fred_macro_regime_input(
    db: Session = Depends(get_db),
    _current_user: dict = Depends(get_current_user),
) -> ApiResponse[dict]:
    try:
        result = apply_nfci_macro_input(db)
    except ValueError as exc:
        raise PublicApiError(
            status_code=409,
            code="REGIME_PROVIDER_INPUT_BLOCKED",
            message=str(exc),
            provider="FRED",
        ) from exc
    return ApiResponse(
        data=result,
        meta=ApiMeta(
            source="FRED",
            is_stale=result["is_stale"],
            warnings=result["warnings"],
            confidence="low" if result["is_stale"] else "high",
        ),
    )
