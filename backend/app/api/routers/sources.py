from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.helpers import create_record, delete_record, get_or_404, has_matching_record, update_record
from app.api.schemas import ApiResponse, SourceCreate, SourceRead, SourceUpdate
from app.db.session import get_db
from app.models import RawDocument, Source


router = APIRouter()


@router.post("/sources", response_model=ApiResponse[SourceRead], status_code=status.HTTP_201_CREATED)
def create_source(payload: SourceCreate, db: Session = Depends(get_db)) -> Source:
    return ApiResponse(data=create_record(db, Source, payload))


@router.get("/sources", response_model=ApiResponse[list[SourceRead]])
def list_sources(db: Session = Depends(get_db)) -> list[Source]:
    return ApiResponse(data=list(db.scalars(select(Source).order_by(Source.id))))


@router.get("/sources/{source_id}", response_model=ApiResponse[SourceRead])
def get_source(source_id: int, db: Session = Depends(get_db)) -> Source:
    return ApiResponse(data=get_or_404(db, Source, source_id))


@router.patch("/sources/{source_id}", response_model=ApiResponse[SourceRead])
def update_source(source_id: int, payload: SourceUpdate, db: Session = Depends(get_db)) -> Source:
    return ApiResponse(data=update_record(db, get_or_404(db, Source, source_id), payload))


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_source(source_id: int, db: Session = Depends(get_db)) -> None:
    source = get_or_404(db, Source, source_id)
    if has_matching_record(db, select(RawDocument.id).where(RawDocument.source_id == source_id)):
        raise HTTPException(
            status_code=409,
            detail="Source cannot be deleted while it has linked raw documents. Delete linked documents first or mark the source inactive.",
        )
    delete_record(db, source)
