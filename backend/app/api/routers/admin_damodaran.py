from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.damodaran import DamodaranDatasetFile
from app.services.damodaran_parser import parse_damodaran_workbook
from app.services.damodaran_dataset_versions import source_provenance_from_bytes
from app.schemas.common import ApiResponse
from app.api.errors import PublicApiError
from app.services.workbook_safety import MAX_WORKBOOK_BYTES, validate_workbook_bytes

router = APIRouter(
    prefix="/api/admin/damodaran",
    tags=["admin_damodaran"],
    dependencies=[Depends(get_current_user)],
)

@router.post("/import", response_model=ApiResponse[dict])
async def import_damodaran_dataset(
    file: UploadFile = File(...),
    dataset_code: str = Form(...),
    country: str = Form(None),
    region: str = Form(None),
    db: Session = Depends(get_db)
):
    filename = file.filename or ""
    if not filename.lower().endswith((".xls", ".xlsx")):
        raise HTTPException(status_code=400, detail="Only .xls or .xlsx files are supported")

    try:
        contents = await file.read(MAX_WORKBOOK_BYTES + 1)
    finally:
        await file.close()
    validate_workbook_bytes(contents)

    try:
        results = parse_damodaran_workbook(contents)
    except Exception as exc:
        raise PublicApiError(
            status_code=422,
            code="DAMODARAN_WORKBOOK_PARSE_FAILED",
            message="The workbook could not be parsed. Verify its format and sheet structure.",
            field="file",
        ) from exc

    provenance = source_provenance_from_bytes(filename, contents)
    record = DamodaranDatasetFile(
        uploaded_filename=filename,
        dataset_code=dataset_code,
        country=country,
        region=region,
        source_file_type=filename.rsplit('.', 1)[-1].lower(),
        source_sha256=provenance.source_sha256,
        source_byte_size=provenance.source_byte_size,
        source_as_of=provenance.source_as_of,
        date_confidence=provenance.date_confidence,
        canonical_source_path=provenance.canonical_source_path,
        import_kind="metadata_only",
        is_active=False,
        notes=f"Parsed {len(results)} sheets successfully."
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    sheet_summaries = {
        name: len(data["records"]) for name, data in results.items()
    }

    return ApiResponse(data={
        "file_id": record.id,
        "dataset_code": dataset_code,
        "sheets_parsed": list(results.keys()),
        "records_per_sheet": sheet_summaries,
        "metadata": {name: data["metadata"] for name, data in results.items()},
        "source_sha256": provenance.source_sha256,
        "source_as_of": provenance.source_as_of,
        "date_confidence": provenance.date_confidence,
        "import_kind": "metadata_only",
    })

@router.get("/files", response_model=ApiResponse[list[dict]])
def list_damodaran_files(db: Session = Depends(get_db)):
    files = db.scalars(
        select(DamodaranDatasetFile)
        .order_by(DamodaranDatasetFile.id.desc())
    ).all()

    data = []
    for f in files:
        data.append({
            "id": f.id,
            "filename": f.uploaded_filename,
            "dataset_code": f.dataset_code,
            "country": f.country,
            "region": f.region,
            "created_at": f.imported_at,
            "source_sha256": f.source_sha256,
            "source_byte_size": f.source_byte_size,
            "source_as_of": f.source_as_of,
            "date_confidence": f.date_confidence,
            "canonical_source_path": f.canonical_source_path,
            "import_kind": f.import_kind,
            "is_active": f.is_active,
            "superseded_at": f.superseded_at,
            "row_count": f.row_count,
            "notes": f.notes
        })
    return ApiResponse(data=data)

@router.post("/{file_id}/rollback", response_model=ApiResponse[dict])
def rollback_damodaran_import(file_id: int, db: Session = Depends(get_db)):
    record = db.scalar(select(DamodaranDatasetFile).where(DamodaranDatasetFile.id == file_id))
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    if record.import_kind == "typed" or record.is_active:
        raise PublicApiError(
            status_code=409,
            code="DAMODARAN_VERSION_DELETE_BLOCKED",
            message=(
                "Active or typed Damodaran versions are preserved for auditability. "
                "Only inactive metadata-only uploads can be deleted here."
            ),
        )

    db.delete(record)
    db.commit()

    return ApiResponse(data={"success": True, "message": f"Rolled back file {file_id}"})

@router.get("/compare", response_model=ApiResponse[dict])
def compare_benchmarks(file_id_a: int, file_id_b: int, db: Session = Depends(get_db)):
    # Mocking response structure for comparison
    return ApiResponse(data={
        "status": "mock",
        "comparison": {
            "implied_erp": {"diff": 0.005, "version_a": 0.045, "version_b": 0.050},
            "default_spread": {"diff": -0.001, "version_a": 0.015, "version_b": 0.014}
        }
    })
