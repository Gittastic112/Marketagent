from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.helpers import create_record, delete_record, get_or_404, has_matching_record, update_record, validate_event_refs
from app.api.schemas import (
    ApiMeta,
    ApiResponse,
    EvidenceTrailRead,
    EventCreate,
    EventEvidenceReferenceCreate,
    EventEvidenceReferenceRead,
    EventEvidenceResolutionCreate,
    EventEvidenceResolutionSearchRead,
    EventRead,
    EventUpdate,
)
from app.db.session import get_db
from app.models import Alert, Event, EventEvidenceReference, RawDocument
from app.services.evidence_trail_service import build_evidence_trail
from app.services.event_evidence_resolution import (
    EvidenceResolutionError,
    create_manual_exact_evidence,
    search_event_evidence,
)
from app.services.pdf_page_rendering import validate_pdf_region_against_asset


router = APIRouter()


def _raise_resolution_error(exc: EvidenceResolutionError) -> None:
    from app.api.errors import PublicApiError

    raise PublicApiError(
        status_code=exc.status_code,
        code=exc.code,
        message=exc.message,
    ) from exc


def _evidence_reference_read(
    db: Session,
    reference: EventEvidenceReference,
) -> EventEvidenceReferenceRead:
    pdf_region_status = "not_applicable"
    if reference.locator_type == "pdf_region":
        pdf_region_status = "invalid"
        document = db.get(RawDocument, reference.raw_document_id)
        if document and document.asset:
            try:
                validate_pdf_region_against_asset(
                    reference.bounding_box_json,
                    source_page=reference.source_page,
                    content=document.asset.content,
                )
                pdf_region_status = "valid"
            except (IndexError, ValueError):
                pass
    return EventEvidenceReferenceRead.model_validate(reference).model_copy(
        update={"pdf_region_status": pdf_region_status}
    )


@router.post("/events", response_model=ApiResponse[EventRead], status_code=status.HTTP_201_CREATED)
def create_event(payload: EventCreate, db: Session = Depends(get_db)) -> Event:
    validate_event_refs(db, payload)
    return ApiResponse(data=create_record(db, Event, payload))


@router.get("/events", response_model=ApiResponse[list[EventRead]])
def list_events(db: Session = Depends(get_db)) -> list[Event]:
    return ApiResponse(data=list(db.scalars(select(Event).order_by(Event.id))))


@router.get("/events/{event_id}", response_model=ApiResponse[EventRead])
def get_event(event_id: int, db: Session = Depends(get_db)) -> Event:
    return ApiResponse(data=get_or_404(db, Event, event_id))


@router.patch("/events/{event_id}", response_model=ApiResponse[EventRead])
def update_event(event_id: int, payload: EventUpdate, db: Session = Depends(get_db)) -> Event:
    validate_event_refs(db, payload)
    return ApiResponse(data=update_record(db, get_or_404(db, Event, event_id), payload))


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int, db: Session = Depends(get_db)) -> None:
    event = get_or_404(db, Event, event_id)
    if has_matching_record(db, select(Alert.id).where(Alert.event_id == event_id)):
        raise HTTPException(
            status_code=409,
            detail="Event cannot be deleted while it has linked alerts. Delete linked alerts first.",
        )
    delete_record(db, event)


def _validate_evidence_reference(
    event: Event,
    document: RawDocument,
    payload: EventEvidenceReferenceCreate,
) -> None:
    if event.company_id and document.company_id and event.company_id != document.company_id:
        raise HTTPException(status_code=422, detail="Evidence document belongs to another company")
    if payload.locator_type == "text_span":
        assert payload.start_char is not None and payload.end_char is not None and payload.quote
        if not document.raw_text:
            raise HTTPException(status_code=422, detail="Evidence document has no stored source text")
        if payload.end_char > len(document.raw_text):
            raise HTTPException(status_code=422, detail="Evidence span exceeds the stored source text")
        if document.raw_text[payload.start_char:payload.end_char] != payload.quote:
            raise HTTPException(status_code=422, detail="Evidence quote does not match the stored source span")
    if payload.locator_type == "pdf_region":
        if document.asset is None:
            raise HTTPException(status_code=422, detail="Evidence document has no stored PDF asset")
        assert payload.source_page is not None
        if payload.source_page > document.asset.page_count:
            raise HTTPException(status_code=422, detail="Evidence page exceeds the stored PDF page count")
        try:
            geometry = validate_pdf_region_against_asset(
                payload.bounding_box_json,
                source_page=payload.source_page,
                content=document.asset.content,
            )
        except (IndexError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        payload.bounding_box_json = geometry.as_json()


@router.post(
    "/events/{event_id}/evidence-references",
    response_model=ApiResponse[EventEvidenceReferenceRead],
    status_code=status.HTTP_201_CREATED,
)
def create_event_evidence_reference(
    event_id: int,
    payload: EventEvidenceReferenceCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[EventEvidenceReferenceRead]:
    event = db.scalar(select(Event).where(Event.id == event_id).with_for_update())
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    document = get_or_404(db, RawDocument, payload.raw_document_id)
    _validate_evidence_reference(event, document, payload)
    reference = EventEvidenceReference(
        event_id=event.id,
        created_by_user_id=current_user["id"],
        origin="manual_review",
        **payload.model_dump(),
    )
    db.add(reference)
    db.commit()
    db.refresh(reference)
    return ApiResponse(data=_evidence_reference_read(db, reference))


@router.get(
    "/events/{event_id}/evidence-references",
    response_model=ApiResponse[list[EventEvidenceReferenceRead]],
)
def list_event_evidence_references(
    event_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse[list[EventEvidenceReferenceRead]]:
    get_or_404(db, Event, event_id)
    references = list(
        db.scalars(
            select(EventEvidenceReference)
            .where(EventEvidenceReference.event_id == event_id)
            .order_by(EventEvidenceReference.id)
        )
    )
    return ApiResponse(data=[_evidence_reference_read(db, reference) for reference in references])


@router.get(
    "/evidence-references/{reference_id}",
    response_model=ApiResponse[EventEvidenceReferenceRead],
)
def get_event_evidence_reference(
    reference_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse[EventEvidenceReferenceRead]:
    reference = get_or_404(db, EventEvidenceReference, reference_id)
    return ApiResponse(data=_evidence_reference_read(db, reference))


@router.delete(
    "/evidence-references/{reference_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_event_evidence_reference(
    reference_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> None:
    reference = db.scalar(
        select(EventEvidenceReference).where(
            EventEvidenceReference.id == reference_id,
            EventEvidenceReference.created_by_user_id == current_user["id"],
        )
    )
    if reference is None:
        raise HTTPException(status_code=404, detail="Evidence reference not found")
    delete_record(db, reference)


@router.get(
    "/events/{event_id}/evidence-resolution/search",
    response_model=ApiResponse[EventEvidenceResolutionSearchRead],
)
def search_event_evidence_resolution(
    event_id: int,
    q: str = Query(min_length=8, max_length=300),
    context_chars: int = Query(default=180, ge=40, le=300),
    limit: int = Query(default=25, ge=1, le=25),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[dict[str, Any]]:
    try:
        result = search_event_evidence(
            db,
            event_id=event_id,
            query=q,
            context_chars=context_chars,
            limit=limit,
        )
    except EvidenceResolutionError as exc:
        _raise_resolution_error(exc)
    return ApiResponse(
        data=result,
        meta=ApiMeta(
            source="stored_document_text",
            confidence="high",
            warnings=result["limitations"],
        ),
    )


@router.post(
    "/events/{event_id}/evidence-resolution",
    response_model=ApiResponse[EventEvidenceReferenceRead],
    status_code=status.HTTP_201_CREATED,
)
def resolve_event_evidence(
    event_id: int,
    payload: EventEvidenceResolutionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[EventEvidenceReferenceRead]:
    try:
        reference = create_manual_exact_evidence(
            db,
            event_id=event_id,
            user_id=current_user["id"],
            payload=payload,
        )
    except EvidenceResolutionError as exc:
        _raise_resolution_error(exc)
    return ApiResponse(
        data=_evidence_reference_read(db, reference),
        meta=ApiMeta(
            source="manual_exact_source_selection",
            confidence="high",
            warnings=["Locator confidence is high; the evidence claim still requires investment judgment."],
        ),
    )


from app.api.schemas import EventLinkCreate
from app.models.event import EventCorroboration, EventContradiction

@router.post(
    "/events/{event_id}/corroborations",
    response_model=ApiResponse[dict[str, str]],
    status_code=status.HTTP_201_CREATED,
)
def add_corroboration(event_id: int, payload: EventLinkCreate, db: Session = Depends(get_db)):
    get_or_404(db, Event, event_id)
    get_or_404(db, Event, payload.target_event_id)
    if event_id == payload.target_event_id:
        raise HTTPException(status_code=422, detail="An event cannot corroborate itself")
    if db.get(EventCorroboration, (event_id, payload.target_event_id)) is not None:
        raise HTTPException(status_code=409, detail="Corroboration already exists")
    link = EventCorroboration(source_event_id=event_id, target_event_id=payload.target_event_id)
    db.add(link)
    db.commit()
    return ApiResponse(data={"message": "Corroboration added"})

@router.delete("/events/{event_id}/corroborations/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_corroboration(event_id: int, target_id: int, db: Session = Depends(get_db)):
    link = db.scalar(select(EventCorroboration).where(
        EventCorroboration.source_event_id == event_id,
        EventCorroboration.target_event_id == target_id
    ))
    if not link:
        raise HTTPException(status_code=404, detail="Corroboration not found")
    db.delete(link)
    db.commit()

@router.post(
    "/events/{event_id}/contradictions",
    response_model=ApiResponse[dict[str, str]],
    status_code=status.HTTP_201_CREATED,
)
def add_contradiction(event_id: int, payload: EventLinkCreate, db: Session = Depends(get_db)):
    get_or_404(db, Event, event_id)
    get_or_404(db, Event, payload.target_event_id)
    if event_id == payload.target_event_id:
        raise HTTPException(status_code=422, detail="An event cannot contradict itself")
    if db.get(EventContradiction, (event_id, payload.target_event_id)) is not None:
        raise HTTPException(status_code=409, detail="Contradiction already exists")
    link = EventContradiction(source_event_id=event_id, target_event_id=payload.target_event_id)
    db.add(link)
    db.commit()
    return ApiResponse(data={"message": "Contradiction added"})

@router.delete("/events/{event_id}/contradictions/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_contradiction(event_id: int, target_id: int, db: Session = Depends(get_db)):
    link = db.scalar(select(EventContradiction).where(
        EventContradiction.source_event_id == event_id,
        EventContradiction.target_event_id == target_id
    ))
    if not link:
        raise HTTPException(status_code=404, detail="Contradiction not found")
    db.delete(link)
    db.commit()

from app.services.impact_classifier import classify_event_impact
from app.api.ai_errors import ai_output_meta, public_ai_error
from app.api.schemas import AIPrivacyAcknowledgement
from app.services.ai_contract import AIExecutionError, require_privacy_disclosure

@router.post(
    "/events/{event_id}/classify-impact",
    response_model=ApiResponse[dict[str, Any]],
    status_code=status.HTTP_200_OK,
)
def classify_impact(
    event_id: int,
    acknowledgement: AIPrivacyAcknowledgement,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    get_or_404(db, Event, event_id)
    try:
        require_privacy_disclosure(acknowledgement.privacy_disclosure_version)
        impacts, ai_output = classify_event_impact(
            db,
            event_id,
            user_id=current_user["id"],
        )
    except AIExecutionError as exc:
        raise public_ai_error(exc) from exc
    if ai_output is None:
        return ApiResponse(
            data={
                "proposed_impacts": [],
                "applied_count": 0,
                "message": "No owned active thesis assumptions were available.",
            }
        )
    return ApiResponse(
        data={
            "proposed_impacts": impacts,
            "applied_count": 0,
            "message": "Review proposed impacts before applying them through the thesis impact workflow.",
        },
        meta=ai_output_meta(ai_output),
    )

@router.get("/events/{event_id}/evidence-trail", response_model=ApiResponse[EvidenceTrailRead])
def get_evidence_trail(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[EvidenceTrailRead]:
    event = get_or_404(db, Event, event_id)
    trail = build_evidence_trail(db, user_id=current_user["id"], event=event)
    return ApiResponse(
        data=trail,
        meta=ApiMeta(
            source=trail.source.name if trail.source else "internal",
            last_updated=trail.source_timestamp,
            warnings=trail.warnings,
            confidence=trail.confidence,
        ),
    )
