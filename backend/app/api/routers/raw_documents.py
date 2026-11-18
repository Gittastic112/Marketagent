from datetime import UTC, date, datetime, time
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.helpers import create_record, delete_record, get_or_404, update_record, validate_raw_document_refs
from app.api.schemas import (
    ApiResponse,
    RawDocumentCreate,
    RawDocumentRead,
    RawDocumentSummaryRead,
    RawDocumentUpdate,
)
from app.db.session import get_db
from app.models import Company, RawDocument, FinancialExtractionCandidate
from app.schemas.document_library import DocumentLibraryRead
from app.services.source_preservation import changes_source_evidence, has_document_dependents


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


@router.get("/raw-documents/library", response_model=ApiResponse[DocumentLibraryRead])
def document_library(q: str = Query(default="", max_length=200), company_id: int | None = Query(default=None, gt=0),
    document_type: str = Query(default="", max_length=80),
    review: Literal["all", "needs_review", "promoted"] = "all",
    published_from: date | None = None, published_to: date | None = None,
    offset: int = Query(default=0, ge=0, le=100000), limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db)):
    query = raw_document_summary_query()
    if q.strip():
        query = query.where(RawDocument.title.icontains(q.strip(), autoescape=True))
    if company_id is not None:
        query = query.where(RawDocument.company_id == company_id)
    if document_type:
        query = query.where(RawDocument.document_type == document_type)
    if published_from and published_to and published_from > published_to:
        raise HTTPException(status_code=422, detail="Publication range must start before it ends")
    if published_from:
        query = query.where(RawDocument.published_at >= datetime.combine(published_from, time.min, UTC))
    if published_to:
        query = query.where(RawDocument.published_at <= datetime.combine(published_to, time.max, UTC))
    if review != "all":
        statuses = ["promoted"] if review == "promoted" else ["needs_review", "reviewed", "overridden"]
        query = query.where(select(FinancialExtractionCandidate.id).where(
            FinancialExtractionCandidate.raw_document_id == RawDocument.id,
            FinancialExtractionCandidate.review_status.in_(statuses)).exists())
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.execute(query.order_by(RawDocument.ingested_at.desc(), RawDocument.id.desc()).offset(offset).limit(limit)).mappings()
    return ApiResponse(data=DocumentLibraryRead(items=[RawDocumentSummaryRead.model_validate(dict(row)) for row in items],
        total=total, offset=offset, limit=limit))


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
    document = get_or_404(db, RawDocument, raw_document_id)
    db.refresh(document, with_for_update=True)
    if changes_source_evidence(document, payload.model_dump(exclude_unset=True)):
        raise HTTPException(status_code=409, detail="Source evidence cannot be overwritten. Preserve this document and import corrected evidence separately.")
    validate_raw_document_refs(db, payload)
    return ApiResponse(data=update_record(db, document, payload))


@router.delete("/raw-documents/{raw_document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_raw_document(raw_document_id: int, db: Session = Depends(get_db)) -> None:
    raw_document = get_or_404(db, RawDocument, raw_document_id)
    db.refresh(raw_document, with_for_update=True)
    if has_document_dependents(db, raw_document_id):
        raise HTTPException(
            status_code=409,
            detail="Raw document cannot be deleted while retained evidence depends on it.",
        )
    delete_record(db, raw_document)


from app.api.schemas import FilingSectionRead, FilingSectionDiffRead, ApiMeta
from app.models.sec_parsing import FilingSection, FilingSectionDiff
from app.services.sec_parsing import parse_sec_filing
from app.services.sec_diff import generate_section_diffs, section_diffs_need_refresh
from app.services.event_extraction import _find_prior_comparable_filing

@router.get("/raw-documents/{raw_document_id}/sections", response_model=ApiResponse[list[FilingSectionRead]])
def get_raw_document_sections(raw_document_id: int, db: Session = Depends(get_db)) -> ApiResponse[list[FilingSectionRead]]:
    document = get_or_404(db, RawDocument, raw_document_id)
    sections = list(db.scalars(select(FilingSection).where(FilingSection.raw_document_id == raw_document_id).order_by(FilingSection.id)))

    actual_prior_document = _find_prior_comparable_filing(db, document)
    is_stale = section_diffs_need_refresh(db, sections, actual_prior_document)
    warnings = ["Filing comparisons are missing or outdated. Run parser again to update."] if is_stale else []

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

    # Serialize shared predecessor parsing and keep existing section identities.
    if document.company_id is not None:
        db.scalar(select(Company).where(Company.id == document.company_id).with_for_update())
    else:
        db.scalar(select(RawDocument).where(RawDocument.id == document.id).with_for_update())
    existing_sections = list(db.scalars(select(FilingSection).where(FilingSection.raw_document_id == document.id)))
    sections = existing_sections or parse_sec_filing(db, document)
    db.flush()

    # Try diffing
    prior_document = _find_prior_comparable_filing(db, document)
    if prior_document:
        prior_sections = list(db.scalars(select(FilingSection).where(FilingSection.raw_document_id == prior_document.id)))
        if not prior_sections:
            parse_sec_filing(db, prior_document)
            db.flush()

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
