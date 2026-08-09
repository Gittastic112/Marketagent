from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.market_regime_engine import MarketRegimeEngine
from app.api.dependencies import get_current_user
from app.api.schemas import (
    ApiMeta,
    ApiResponse,
    MarketRegimeInputCreate,
    MarketRegimeInputRead,
    MarketRegimeScoreRead,
)
from app.models.market_regime_input import MarketRegimeInput

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
            source="manual",
            last_updated=score.created_at,
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
        source_url=payload.source_url
    )
    db.add(db_input)
    db.commit()
    db.refresh(db_input)
    MarketRegimeEngine(db).calculate_regime_score()
    return ApiResponse(
        data=db_input,
        meta=ApiMeta(
            source="manual",
            last_updated=db_input.created_at,
            confidence="medium",
        ),
    )
