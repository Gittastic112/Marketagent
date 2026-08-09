from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.schemas import ApiResponse, DocumentAssetRead, PdfFinancialExtractionResultRead
from app.db.session import get_db
from app.models import Company, DocumentAsset, RawDocument
from app.services.pdf_financial_extraction import (
    MAX_PDF_BYTES,
    PDF_EXTRACTION_METHOD,
    PDF_SOURCE_NAME,
    ensure_pdf_source,
    ingest_pdf_financials,
    parse_pdf_financial_tables,
    parse_pdf_page_ranges,
    validate_pdf_upload,
    validate_pdf_source_url,
)
from app.services.processing_runs import complete_processing_run, fail_processing_run, start_processing_run
from app.services.pdf_page_rendering import (
    MAX_RENDER_SCALE,
    MIN_RENDER_SCALE,
    render_pdf_page_png,
)


router = APIRouter(tags=["pdf-filings"])


@router.post(
    "/api/companies/{company_id}/filings/pdf",
    response_model=ApiResponse[PdfFinancialExtractionResultRead],
    status_code=status.HTTP_201_CREATED,
)
def upload_pdf_filing(
    company_id: int,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    title: str | None = Form(None),
    published_at: datetime | None = Form(None),
    source_url: str | None = Form(None),
    page_ranges: str | None = Form(None),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> ApiResponse[PdfFinancialExtractionResultRead]:
    company = db.get(Company, company_id)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")

    source = ensure_pdf_source(db)
    run = start_processing_run(
        db,
        run_type="pdf_filing_upload",
        source_type=source.source_type,
        source_id=source.id,
        company_id=company_id,
        metadata={"parser": PDF_EXTRACTION_METHOD},
    )

    try:
        content = file.file.read(MAX_PDF_BYTES + 1)
        upload = validate_pdf_upload(file.filename, file.content_type, content)
        normalized_source_url = validate_pdf_source_url(source_url)
        page_numbers = parse_pdf_page_ranges(page_ranges)
        content_hash = f"pdf-filing:{company_id}:{upload.sha256}"
        if db.scalar(select(RawDocument.id).where(RawDocument.content_hash == content_hash)) is not None:
            complete_processing_run(
                db,
                run,
                fetched_count=1,
                skipped_duplicate_count=1,
                metadata_patch={
                    "original_filename": upload.filename,
                    "file_size_bytes": len(upload.content),
                    "sha256": upload.sha256,
                    "source_url": normalized_source_url,
                    "scanned_pages": list(page_numbers or ()),
                },
            )
            raise HTTPException(status_code=409, detail="This PDF has already been uploaded for the company.")

        candidate_period_type = {
            "annual_report": "annual",
            "quarterly_result": "quarterly",
        }.get(document_type, "unknown")
        parsed = parse_pdf_financial_tables(
            upload.content,
            page_numbers=page_numbers,
            period_type=candidate_period_type,
        )
        result = ingest_pdf_financials(
            db,
            company=company,
            source=source,
            upload=upload,
            parsed=parsed,
            document_type=document_type,
            title=title,
            published_at=published_at,
            source_url=normalized_source_url,
        )
        complete_processing_run(
            db,
            run,
            fetched_count=parsed.table_count,
            created_count=result.created_count,
            metadata_patch={
                "raw_document_id": result.raw_document_id,
                "asset_id": result.asset.id,
                "original_filename": upload.filename,
                "file_size_bytes": len(upload.content),
                "sha256": upload.sha256,
                "page_count": parsed.page_count,
                "scanned_page_count": len(parsed.scanned_pages),
                "scanned_pages": list(parsed.scanned_pages),
                "table_count": parsed.table_count,
                "source_url": normalized_source_url,
                "warnings": list(parsed.warnings),
            },
        )
        response = ApiResponse(data=result)
        response.meta.warnings.extend(result.warnings)
        response.meta.source = PDF_SOURCE_NAME
        response.meta.confidence = "medium"
        return response
    except HTTPException as exc:
        db.rollback()
        persisted = db.get(type(run), run.id)
        if persisted is not None and persisted.status == "running":
            fail_processing_run(db, persisted, error_type="request_error", message=str(exc.detail))
        raise
    except Exception as exc:
        db.rollback()
        persisted = db.get(type(run), run.id)
        if persisted is not None and persisted.status == "running":
            fail_processing_run(db, persisted, error_type=type(exc).__name__)
        raise HTTPException(status_code=500, detail="Unable to process the uploaded PDF.") from exc


@router.get(
    "/api/raw-documents/{raw_document_id}/asset",
    response_model=ApiResponse[DocumentAssetRead],
)
def get_document_asset(
    raw_document_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> ApiResponse[DocumentAssetRead]:
    asset = db.scalar(
        select(DocumentAsset).where(DocumentAsset.raw_document_id == raw_document_id)
    )
    if asset is None:
        raise HTTPException(status_code=404, detail="Document asset not found")
    return ApiResponse(data=asset)


@router.get(
    "/api/raw-documents/{raw_document_id}/asset/content",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
def stream_document_asset(
    raw_document_id: int,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> Response:
    asset = db.scalar(
        select(DocumentAsset).where(DocumentAsset.raw_document_id == raw_document_id)
    )
    if asset is None:
        raise HTTPException(status_code=404, detail="Document asset not found")
    encoded_filename = quote(asset.original_filename, safe="")
    return Response(
        content=asset.content,
        media_type="application/pdf",
        headers={
            "Cache-Control": "private, no-store",
            "Content-Disposition": f"inline; filename=\"filing.pdf\"; filename*=UTF-8''{encoded_filename}",
            "Content-Length": str(asset.size_bytes),
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get(
    "/api/raw-documents/{raw_document_id}/asset/pages/{page_number}.png",
    response_class=Response,
    responses={200: {"content": {"image/png": {}}}},
)
def render_document_asset_page(
    raw_document_id: int,
    page_number: int,
    scale: float = Query(1.5, ge=MIN_RENDER_SCALE, le=MAX_RENDER_SCALE),
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> Response:
    asset = db.scalar(
        select(DocumentAsset).where(DocumentAsset.raw_document_id == raw_document_id)
    )
    if asset is None:
        raise HTTPException(status_code=404, detail="Document asset not found")
    if page_number < 1 or page_number > asset.page_count:
        raise HTTPException(status_code=404, detail="Document page not found")
    try:
        content = render_pdf_page_png(asset.content, page_number, scale)
    except (IndexError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="Document page could not be rendered safely") from exc
    return Response(
        content=content,
        media_type="image/png",
        headers={
            "Cache-Control": "private, no-store",
            "Content-Disposition": f'inline; filename="evidence-page-{page_number}.png"',
            "Content-Length": str(len(content)),
            "X-Content-Type-Options": "nosniff",
        },
    )
