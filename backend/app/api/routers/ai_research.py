import json
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.ai_errors import ai_output_meta, public_ai_error
from app.api.dependencies import get_current_user
from app.schemas.common import ApiResponse
from app.db.session import get_db
from app.services.ai_citations import extract_source_ids, validate_ai_citations
from app.services.ai_contract import AIExecutionError
from app.services.ai_research_assistant import AIResearchAssistant
from app.services.dcf_variable_mapper import map_event_to_dcf_variables

router = APIRouter(prefix="/ai/research", tags=["ai-research"])

class SummarizeRequest(BaseModel):
    document_id: int
    user_task: str

class QuestionRequest(BaseModel):
    document_id: int
    user_question: str

class MapEventRequest(BaseModel):
    event_text: str
    event_id: int | None = None

@router.post("/summarize", response_model=ApiResponse[dict[str, Any]])
def summarize_evidence(
    req: SummarizeRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generates a safe summary of a source document."""
    assistant = AIResearchAssistant(db, user_id=current_user["id"])
    try:
        result = assistant.summarize_evidence(req.document_id, req.user_task)
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
        result = assistant.answer_question_on_evidence(req.document_id, req.user_question)
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
        result = map_event_to_dcf_variables(
            db=db,
            event_text=req.event_text,
            event_id=req.event_id,
            user_id=current_user["id"],
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

    return ApiResponse(
        data=data,
        meta=ai_output_meta(result),
    )
