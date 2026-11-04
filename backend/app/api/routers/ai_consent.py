"""Authenticated management of explicit, owner-scoped external AI permissions."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.errors import PublicApiError
from app.db.session import get_db
from app.schemas.ai_consent import AIConsentDecisionRead, AIConsentDecisionRequest, AIConsentHistory, AIConsentOverview
from app.schemas.common import ApiResponse
from app.services.ai_consent import ConsentPolicyError, consent_history, consent_overview, decision_read, record_decision


router = APIRouter(prefix="/ai/consent", tags=["ai-consent"])


@router.get("", response_model=ApiResponse[AIConsentOverview])
def overview(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return ApiResponse(data=consent_overview(db, user["id"]))


@router.get("/history", response_model=ApiResponse[AIConsentHistory])
def history(cursor: int | None = Query(default=None, gt=0), limit: int = Query(default=25, ge=1, le=100),
            db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return ApiResponse(data=consent_history(db, user["id"], cursor=cursor, limit=limit))


@router.post("/decisions", response_model=ApiResponse[AIConsentDecisionRead])
def decide(payload: AIConsentDecisionRequest, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    try:
        row = record_decision(db, user["id"], payload)
    except ConsentPolicyError as exc:
        raise PublicApiError(status_code=exc.status_code, code=exc.code, message=exc.message) from exc
    return ApiResponse(data=decision_read(row))
