from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.ai_errors import public_ai_error
from app.api.dependencies import get_current_user
from app.schemas.common import ApiResponse
from app.db.session import get_db
from app.schemas.brief_sources import BriefAnalysisRequest, BriefSourceCreate, BriefSourceLifecycleWrite, BriefSourcePage, BriefSourceQuery, BriefSourceRead
from app.schemas.brief_triage import BriefTriageRead, BriefReviewWrite, BriefReviewRead, BriefReviewDetail
from app.schemas.brief_sources import ValuationField
from app.services.brief_comparison_reviews import latest_reviews, save_review, review_history, review_detail
from app.services.brief_source_lifecycle import set_source_lifecycle
from app.services.brief_source_triage import compare_sources
from app.services.ai_contract import AIExecutionError
from app.services.brief_source_extraction import MAX_BRIEF_PDF_BYTES
from app.services.brief_sources import analyze_source, create_source, list_sources, owned_source, search_sources, source_read

def private_cache(response: Response):
    response.headers["Cache-Control"] = "private, no-store"


router = APIRouter(prefix="/brief-sources", tags=["brief-sources"], dependencies=[Depends(private_cache)])


@router.get("", response_model=ApiResponse[list[BriefSourceRead]])
def list_brief_sources(company_id: int | None = Query(None, gt=0), limit: int = Query(20, ge=1, le=50),
                       db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    sources = list_sources(db, user["id"], company_id=company_id, limit=limit)
    return ApiResponse(data=sources, meta={"source": "owned_user_supplied_sources", "is_mock": any(s.is_mock for s in sources)})


@router.get("/search", response_model=ApiResponse[BriefSourcePage])
def search_brief_sources(filters: Annotated[BriefSourceQuery, Query()],
                         db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    page = search_sources(db, user["id"], filters)
    return ApiResponse(data=page, meta={"source": "owned_user_supplied_sources", "is_mock": any(s.is_mock for s in page.items)})


@router.post("", response_model=ApiResponse[BriefSourceRead])
def paste_source(payload: BriefSourceCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return ApiResponse(data=source_read(db, create_source(db, user["id"], payload)))


@router.get("/triage", response_model=ApiResponse[BriefTriageRead])
def compare_brief_sources(company_id: int = Query(..., gt=0), include_mock: bool = False,
                          db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    data = compare_sources(db, user["id"], company_id, include_mock=include_mock)
    data.reviews = latest_reviews(db, user["id"], company_id, include_mock, data.evidence_hash)
    return ApiResponse(data=data, meta={"source": "stored_private_source_comparison", "last_updated": data.computed_at,
        "is_mock": any(source.is_mock for source in data.sources), "warnings": data.warnings,
        "confidence": "not_assessed",
        "status": "partial" if data.coverage.not_examined or data.coverage.excluded else "success"})


@router.post("/triage/reviews", response_model=ApiResponse[BriefReviewRead], status_code=201)
def create_comparison_review(payload: BriefReviewWrite, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return ApiResponse(data=save_review(db, user["id"], payload), meta={"source": "analyst_comparison_review", "is_mock": payload.include_mock})


@router.get("/triage/reviews", response_model=ApiResponse[list[BriefReviewRead]])
def list_comparison_reviews(company_id: int = Query(..., gt=0), field: ValuationField = Query(...), include_mock: bool = False,
    before_id: int | None = Query(None, gt=0), limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return ApiResponse(data=review_history(db, user["id"], company_id, field, include_mock, before_id, limit),
        meta={"source": "analyst_comparison_review", "is_mock": include_mock})


@router.get("/triage/reviews/{review_id}", response_model=ApiResponse[BriefReviewDetail])
def read_comparison_review(review_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    data = review_detail(db, user["id"], review_id)
    return ApiResponse(data=data, meta={"source": "analyst_comparison_review", "is_mock": data.include_mock})


@router.post("/pdf", response_model=ApiResponse[BriefSourceRead])
def upload_source(company_id: int = Form(..., gt=0), title: str = Form(..., min_length=1, max_length=240),
                  source_url: str | None = Form(None, max_length=1000), as_of_date: date | None = Form(None),
                  page_ranges: str | None = Form(None, max_length=200), file: UploadFile = File(...),
                  db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    try:
        payload = BriefSourceCreate(company_id=company_id, title=title, source_url=source_url, as_of_date=as_of_date,
                                    text="PDF content is extracted after upload validation.")
    except ValidationError:
        raise HTTPException(422, "Check the title, company and source date.") from None
    try:
        content = file.file.read(MAX_BRIEF_PDF_BYTES + 1)
        source = create_source(db, user["id"], payload, pdf=content, filename=file.filename or "source.pdf",
                               content_type=file.content_type, page_ranges=page_ranges)
    finally:
        file.file.close()
    return ApiResponse(data=source_read(db, source))


@router.get("/{source_id}", response_model=ApiResponse[dict])
def read_source(source_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    source = owned_source(db, source_id, user["id"])
    return ApiResponse(data={**source_read(db, source).model_dump(), "text": source.content_text})


@router.get("/{source_id}/pdf", response_class=Response, responses={200: {"content": {"application/pdf": {}}}})
def read_source_pdf(source_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    source = owned_source(db, source_id, user["id"])
    if source.source_kind != "pdf" or not source.pdf_bytes:
        raise HTTPException(404, "Original PDF not available")
    return Response(content=source.pdf_bytes, media_type="application/pdf", headers={
        "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff",
        "Content-Disposition": f'inline; filename="brief-source-{source.id}.pdf"',
    })


@router.post("/{source_id}/analyze", response_model=ApiResponse[BriefSourceRead])
def scan_source(source_id: int, payload: BriefAnalysisRequest, db: Session = Depends(get_db),
                user: dict = Depends(get_current_user)):
    try:
        source = analyze_source(db, user["id"], source_id, payload.privacy_disclosure_version)
    except AIExecutionError as exc:
        raise public_ai_error(exc) from exc
    data = source_read(db, source)
    return ApiResponse(data=data, meta={"source": data.provider, "is_mock": data.is_mock, "warnings": data.warnings})


@router.post("/{source_id}/lifecycle", response_model=ApiResponse[BriefSourceRead])
def organize_source(source_id: int, payload: BriefSourceLifecycleWrite, db: Session = Depends(get_db),
                    user: dict = Depends(get_current_user)):
    source = set_source_lifecycle(db, user["id"], source_id, payload)
    data = source_read(db, source)
    return ApiResponse(data=data, meta={"source": "owned_user_supplied_sources", "is_mock": data.is_mock})
