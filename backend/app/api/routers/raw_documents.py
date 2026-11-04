from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.helpers import create_record, delete_record, get_or_404, has_matching_record, update_record, validate_raw_document_refs
from app.api.schemas import (
    ApiResponse,
    RawDocumentCreate,
    RawDocumentRead,
    RawDocumentSummaryRead,
    RawDocumentUpdate,
)
from app.db.session import get_db
from app.models import Event, RawDocument


router = APIRouter()


@router.post("/raw-documents", response_model=ApiResponse[RawDocumentRead], status_code=status.HTTP_201_CREATED)
def create_raw_document(payload: RawDocumentCreate, db: Session = Depends(get_db)) -> RawDocument:
    validate_raw_document_refs(db, payload)
    return ApiResponse(data=create_record(db, RawDocument, payload))


@router.get("/raw-documents", response_model=ApiResponse[list[RawDocumentRead]])
def list_raw_documents(db: Session = Depends(get_db)) -> list[RawDocument]:
    return ApiResponse(data=list(db.scalars(select(RawDocument).order_by(RawDocument.id))))


def raw_document_summary_query():
    return select(
        RawDocument.id,
        RawDocument.company_id,
        RawDocument.source_id,
        RawDocument.document_type,
        RawDocument.title,
        RawDocument.url,
        RawDocument.published_at,
        RawDocument.content_hash,
        RawDocument.ingested_at,
        RawDocument.created_at,
        RawDocument.raw_text.is_not(None).label("has_raw_text"),
    )


@router.get(
    "/raw-documents/summaries",
    response_model=ApiResponse[list[RawDocumentSummaryRead]],
)
def list_raw_document_summaries(
    db: Session = Depends(get_db),
) -> ApiResponse[list[RawDocumentSummaryRead]]:
    rows = db.execute(
        raw_document_summary_query().order_by(RawDocument.id)
    ).mappings()
    return ApiResponse(
        data=[
            RawDocumentSummaryRead.model_validate(dict(row))
            for row in rows
        ]
    )


@router.get(
    "/raw-documents/{raw_document_id}/summary",
    response_model=ApiResponse[RawDocumentSummaryRead],
)
def get_raw_document_summary(
    raw_document_id: int,
    db: Session = Depends(get_db),
) -> ApiResponse[RawDocumentSummaryRead]:
    row = db.execute(
        raw_document_summary_query().where(RawDocument.id == raw_document_id)
    ).mappings().one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="RawDocument not found")
    return ApiResponse(data=RawDocumentSummaryRead.model_validate(dict(row)))


@router.get("/raw-documents/{raw_document_id}", response_model=ApiResponse[RawDocumentRead])
def get_raw_document(raw_document_id: int, db: Session = Depends(get_db)) -> RawDocument:
    return ApiResponse(data=get_or_404(db, RawDocument, raw_document_id))


@router.patch("/raw-documents/{raw_document_id}", response_model=ApiResponse[RawDocumentRead])
def update_raw_document(
    raw_document_id: int,
    payload: RawDocumentUpdate,
    db: Session = Depends(get_db),
) -> RawDocument:
    validate_raw_document_refs(db, payload)
    return ApiResponse(data=update_record(db, get_or_404(db, RawDocument, raw_document_id), payload))


@router.delete("/raw-documents/{raw_document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_raw_document(raw_document_id: int, db: Session = Depends(get_db)) -> None:
    raw_document = get_or_404(db, RawDocument, raw_document_id)
    if has_matching_record(db, select(Event.id).where(Event.raw_document_id == raw_document_id)):
        raise HTTPException(
            status_code=409,
            detail="Raw document cannot be deleted while it has linked events. Delete linked events first.",
        )
    delete_record(db, raw_document)


from app.api.schemas import FilingSectionRead, FilingSectionDiffRead, ApiMeta
from app.models.sec_parsing import FilingSection, FilingSectionDiff
from app.services.sec_parsing import parse_sec_filing
from app.services.sec_diff import generate_section_diffs
from app.services.event_extraction import _find_prior_comparable_filing

@router.get("/raw-documents/{raw_document_id}/sections", response_model=ApiResponse[list[FilingSectionRead]])
def get_raw_document_sections(raw_document_id: int, db: Session = Depends(get_db)) -> ApiResponse[list[FilingSectionRead]]:
    document = get_or_404(db, RawDocument, raw_document_id)
    sections = list(db.scalars(select(FilingSection).where(FilingSection.raw_document_id == raw_document_id).order_by(FilingSection.id)))

    is_stale = False
    warnings = []

    actual_prior_document = _find_prior_comparable_filing(db, document)
    if actual_prior_document and sections:
        for section in sections:
            for diff in section.diffs_as_current:
                if diff.prior_section_id:
                    prior_section_doc_id = db.scalar(select(FilingSection.raw_document_id).where(FilingSection.id == diff.prior_section_id))
                    if prior_section_doc_id != actual_prior_document.id:
                        is_stale = True
                        warnings.append("Diffs are based on an outdated prior filing. Run parser again to update.")
                        break
            if is_stale:
                break

    meta = ApiMeta(is_stale=is_stale, warnings=warnings)
    return ApiResponse(data=sections, meta=meta)


@router.get("/raw-documents/{raw_document_id}/section-diffs", response_model=ApiResponse[list[FilingSectionDiffRead]])
def get_raw_document_section_diffs(raw_document_id: int, db: Session = Depends(get_db)) -> list[FilingSectionDiff]:
    get_or_404(db, RawDocument, raw_document_id)
    return ApiResponse(data=list(db.scalars(select(FilingSectionDiff).join(FilingSection, FilingSectionDiff.current_section_id == FilingSection.id).where(FilingSection.raw_document_id == raw_document_id).order_by(FilingSection.id))))


@router.post(
    "/raw-documents/{raw_document_id}/parse",
    response_model=ApiResponse[dict[str, str]],
    status_code=status.HTTP_200_OK,
)
def parse_raw_document(raw_document_id: int, db: Session = Depends(get_db)) -> ApiResponse[dict[str, str]]:
    document = get_or_404(db, RawDocument, raw_document_id)

    # Check if already parsed
    existing_sections = list(db.scalars(select(FilingSection).where(FilingSection.raw_document_id == document.id)))
    if existing_sections:
        return ApiResponse(data={"status": f"Already parsed into {len(existing_sections)} sections."})

    sections = parse_sec_filing(db, document)
    db.commit()

    # Try diffing
    prior_document = _find_prior_comparable_filing(db, document)
    if prior_document:
        prior_sections = list(db.scalars(select(FilingSection).where(FilingSection.raw_document_id == prior_document.id)))
        if not prior_sections:
            parse_sec_filing(db, prior_document)
            db.commit()

    diffs = generate_section_diffs(db, document, prior_document)
    db.commit()

    return ApiResponse(data={"status": f"Parsed into {len(sections)} sections and generated {len(diffs)} diffs."})


from app.api.schemas import AIPrivacyAcknowledgement, AiOutputRead
from app.models.ai import AiOutput
from app.services.ai import generate_document_summary
from app.api.ai_errors import ai_output_meta, public_ai_error
from app.api.dependencies import get_current_user
from app.services.ai_contract import AIExecutionError, require_privacy_disclosure

@router.get("/raw-documents/{raw_document_id}/ai-outputs", response_model=ApiResponse[list[AiOutputRead]])
def get_raw_document_ai_outputs(
    raw_document_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> list[AiOutput]:
    get_or_404(db, RawDocument, raw_document_id)
    return ApiResponse(data=list(db.scalars(select(AiOutput).where(
        AiOutput.raw_document_id == raw_document_id,
        AiOutput.user_id == current_user["id"],
    ).order_by(AiOutput.id.desc()))))


@router.post("/raw-documents/{raw_document_id}/ai-summary", response_model=ApiResponse[AiOutputRead], status_code=status.HTTP_200_OK)
def create_raw_document_ai_summary(
    raw_document_id: int,
    acknowledgement: AIPrivacyAcknowledgement,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> AiOutput:
    document = get_or_404(db, RawDocument, raw_document_id)
    try:
        require_privacy_disclosure(acknowledgement.privacy_disclosure_version)
        ai_output = generate_document_summary(
            db,
            document,
            user_id=current_user["id"],
            privacy_disclosure_version=acknowledgement.privacy_disclosure_version,
        )
    except AIExecutionError as exc:
        raise public_ai_error(exc) from exc
    return ApiResponse(data=ai_output, meta=ai_output_meta(ai_output))
