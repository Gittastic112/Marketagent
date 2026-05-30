from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api import schemas
from app.db.session import get_db
from app.models.research import ResearchSession, ResearchMessage
from app.api.schemas import ApiResponse

router = APIRouter(tags=["research"])


@router.post("/sessions", response_model=ApiResponse[schemas.ResearchSessionRead])
def create_session(
    payload: schemas.ResearchSessionCreate,
    db: Session = Depends(get_db)
):
    session = ResearchSession(title=payload.title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return ApiResponse(data=session)


@router.get("/sessions", response_model=ApiResponse[list[schemas.ResearchSessionRead]])
def list_sessions(db: Session = Depends(get_db)):
    sessions = db.scalars(select(ResearchSession).order_by(ResearchSession.updated_at.desc())).all()
    return ApiResponse(data=list(sessions))


@router.get("/sessions/{session_id}", response_model=ApiResponse[schemas.ResearchSessionDetail])
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = db.scalar(
        select(ResearchSession)
        .options(selectinload(ResearchSession.messages))
        .where(ResearchSession.id == session_id)
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return ApiResponse(data=session)


@router.post("/sessions/{session_id}/messages", response_model=ApiResponse[schemas.ResearchMessageRead])
def add_message(
    session_id: int,
    payload: schemas.ResearchMessageCreate,
    db: Session = Depends(get_db)
):
    session = db.get(ResearchSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    msg = ResearchMessage(
        session_id=session_id,
        role=payload.role,
        content=payload.content
    )
    db.add(msg)
    
    # Update session updated_at
    from datetime import datetime, timezone
    session.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(msg)
    return ApiResponse(data=msg)
