import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.ai_errors import ai_output_meta, public_ai_error
from app.api.dependencies import get_current_user
from app.schemas.common import ApiResponse
from app.schemas.research import MapEventRequest, QuestionRequest, SummarizeRequest
from app.schemas.ai import AiOutputRead
from app.models import Event
from app.db.session import get_db
from app.services.ai_citations import extract_source_ids, validate_ai_citations
from app.services.ai_contract import AIExecutionError, require_privacy_disclosure
from app.services.ai_research_assistant import AIResearchAssistant
from app.services.dcf_variable_mapper import map_event_to_dcf_variables

router = APIRouter(prefix="/ai/research", tags=["ai-research"])

@router.post("/summarize", response_model=ApiResponse[dict[str, Any]])
def summarize_evidence(
    req: SummarizeRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generates a safe summary of a source document."""
    assistant = AIResearchAssistant(db, user_id=current_user["id"])
    try:
        require_privacy_disclosure(req.privacy_disclosure_version)
        result = assistant.summarize_evidence(req.document_id, req.user_task, req.privacy_disclosure_version)
    except AIExecutionError as exc:
        raise public_ai_error(exc) from exc
    ai_output = result["ai_output"]

    source_ids = extract_source_ids(ai_output.output_text)
    citations = [{"source_id": sid, "quote": None, "start_char": None, "end_char": None} for sid in source_ids]

    validated_citations, status = validate_ai_citations(db, ai_output, citations)
    if ai_output.evaluation_json:
        ai_output.is_blocked = not ai_output.evaluation_json.get("passed", False)
    db.commit()

    return ApiResponse(
        data={
            "output_text": result["output_text"],
            "ai_output_id": result["ai_output_id"],
            "validation_status": status,
            "is_blocked": ai_output.is_blocked,
            "citations": validated_citations
        }
    )

@router.post("/questions", response_model=ApiResponse[dict[str, Any]])
def generate_questions(
    req: QuestionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Answers a question based on a source document."""
    assistant = AIResearchAssistant(db, user_id=current_user["id"])
    try:
        require_privacy_disclosure(req.privacy_disclosure_version)
        result = assistant.answer_question_on_evidence(req.document_id, req.user_question, req.privacy_disclosure_version)
    except AIExecutionError as exc:
        raise public_ai_error(exc) from exc
    ai_output = result["ai_output"]

    source_ids = extract_source_ids(ai_output.output_text)
    citations = [{"source_id": sid, "quote": None, "start_char": None, "end_char": None} for sid in source_ids]

    validated_citations, status = validate_ai_citations(db, ai_output, citations)
    if ai_output.evaluation_json:
        ai_output.is_blocked = not ai_output.evaluation_json.get("passed", False)
    db.commit()

    return ApiResponse(
        data={
            "output_text": result["output_text"],
            "ai_output_id": result["ai_output_id"],
            "validation_status": status,
            "is_blocked": ai_output.is_blocked,
            "citations": validated_citations
        }
    )

@router.post("/map-event-to-dcf", response_model=ApiResponse[dict[str, Any]])
def map_event_endpoint(
    req: MapEventRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Maps an event text to standard DCF variables using AI."""
    try:
        require_privacy_disclosure(req.privacy_disclosure_version)
        if req.event_id is not None:
            event = db.get(Event, req.event_id)
            if event is None:
                raise HTTPException(status_code=404, detail="Event not found")
            if req.event_text != f"{event.title}\n{event.description or ''}":
                raise HTTPException(status_code=409, detail="The event changed. Reload it before requesting an interpretation.")
        result = map_event_to_dcf_variables(
            db=db,
            event_text=req.event_text,
            event_id=req.event_id,
            user_id=current_user["id"],
            privacy_disclosure_version=req.privacy_disclosure_version,
        )
    except AIExecutionError as exc:
        raise public_ai_error(exc) from exc
    # the structured response is inside result.output_text as json string
    try:
        data = json.loads(result.output_text)
    except (TypeError, json.JSONDecodeError):
        data = {"error": "Failed to parse JSON response from AI provider"}
    data["ai_output_id"] = result.id
    data["model_name"] = result.model_name
    data["ai_output"] = AiOutputRead.model_validate(result).model_dump(mode="json")

    return ApiResponse(
        data=data,
        meta=ai_output_meta(result),
    )
