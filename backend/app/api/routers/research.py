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
    
    # If the user sent a message, we should generate an AI response
    if payload.role == "user":
        import os
        from app.providers.ai_provider import GeminiAIProvider
        from app.providers.mock_provider import MockAIProvider
        import logging
        logger = logging.getLogger(__name__)
        
        api_key = os.environ.get("GEMINI_API_KEY")
        is_test = os.environ.get("PYTEST_CURRENT_TEST") is not None
        
        if api_key and not is_test:
            logger.info("Using real AI provider for chat.")
            provider = GeminiAIProvider(api_key=api_key)
        else:
            logger.info("Using mocked AI response for chat.")
            provider = MockAIProvider()
            
        # Build message history for the AI
        db.refresh(session)
        msg_history = [{"role": m.role, "content": m.content} for m in session.messages]
        
        try:
            result = provider.generate_chat_response(messages=msg_history)
        except Exception as e:
            logger.error(f"Provider failed, falling back to mock: {e}")
            provider = MockAIProvider()
            result = provider.generate_chat_response(messages=msg_history)
            
        assistant_msg = ResearchMessage(
            session_id=session_id,
            role="assistant",
            content=result.output_text
        )
        db.add(assistant_msg)
        session.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(assistant_msg)
        # We return the assistant message if it was generated
        return ApiResponse(data=assistant_msg)
        
    return ApiResponse(data=msg)
