from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import ApiResponse, ScoringConfigRead, ScoringConfigUpdate
from app.db.session import get_db
from app.models.scoring_config import ScoringConfig

router = APIRouter()

@router.get("/scoring-config", response_model=ApiResponse[ScoringConfigRead])
def get_scoring_config(db: Session = Depends(get_db)):
    config = db.scalar(select(ScoringConfig).order_by(ScoringConfig.id).limit(1))
    if not config:
        config = ScoringConfig()
        db.add(config)
        db.commit()
        db.refresh(config)
    return ApiResponse(data=config)

@router.patch("/scoring-config", response_model=ApiResponse[ScoringConfigRead])
def update_scoring_config(payload: ScoringConfigUpdate, db: Session = Depends(get_db)):
    config = db.scalar(select(ScoringConfig).order_by(ScoringConfig.id).limit(1))
    if not config:
        config = ScoringConfig()
        db.add(config)
    
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(config, field, value)
        
    db.commit()
    db.refresh(config)
    return ApiResponse(data=config)
