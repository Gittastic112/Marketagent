from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import ApiResponse, ExposureTagCreate, ExposureTagRead
from app.db.session import get_db
from app.models.company import ExposureTag

router = APIRouter()

@router.get("/exposure-tags", response_model=ApiResponse[list[ExposureTagRead]])
def list_exposure_tags(db: Session = Depends(get_db)):
    return ApiResponse(data=list(db.scalars(select(ExposureTag).order_by(ExposureTag.name))))

@router.post("/exposure-tags", response_model=ApiResponse[ExposureTagRead])
def create_exposure_tag(payload: ExposureTagCreate, db: Session = Depends(get_db)):
    tag = ExposureTag(**payload.model_dump())
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return ApiResponse(data=tag)

@router.delete("/exposure-tags/{tag_id}")
def delete_exposure_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.get(ExposureTag, tag_id)
    if tag:
        db.delete(tag)
        db.commit()
    return ApiResponse(data={"status": "ok"})
