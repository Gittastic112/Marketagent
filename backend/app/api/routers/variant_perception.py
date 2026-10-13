from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.helpers import create_record, delete_record, get_or_404, require_reference, update_record
from app.api.schemas import (
    ApiResponse,
    VariantPerceptionCreate, VariantPerceptionRead, VariantPerceptionUpdate
)
from app.db.session import get_db
from app.models.variant_perception import VariantPerception
from app.models.company import Company


router = APIRouter()


@router.post("/variant-perceptions", response_model=ApiResponse[VariantPerceptionRead], status_code=status.HTTP_201_CREATED)
def create_variant_perception(payload: VariantPerceptionCreate, db: Session = Depends(get_db)) -> VariantPerception:
    require_reference(db, Company, payload.company_id, "Company")
    return ApiResponse(data=create_record(db, VariantPerception, payload))


@router.get("/variant-perceptions", response_model=ApiResponse[list[VariantPerceptionRead]])
def list_variant_perceptions(company_id: int | None = None, db: Session = Depends(get_db)) -> list[VariantPerception]:
    query = select(VariantPerception)
    if company_id:
        query = query.where(VariantPerception.company_id == company_id)
    return ApiResponse(data=list(db.scalars(query.order_by(VariantPerception.id.desc()))))


@router.get("/variant-perceptions/{vp_id}", response_model=ApiResponse[VariantPerceptionRead])
def get_variant_perception(vp_id: int, db: Session = Depends(get_db)) -> VariantPerception:
    return ApiResponse(data=get_or_404(db, VariantPerception, vp_id))


@router.patch("/variant-perceptions/{vp_id}", response_model=ApiResponse[VariantPerceptionRead])
def update_variant_perception(
    vp_id: int,
    payload: VariantPerceptionUpdate,
    db: Session = Depends(get_db),
) -> VariantPerception:
    return ApiResponse(data=update_record(db, get_or_404(db, VariantPerception, vp_id), payload))


@router.delete("/variant-perceptions/{vp_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_variant_perception(vp_id: int, db: Session = Depends(get_db)) -> None:
    delete_record(db, get_or_404(db, VariantPerception, vp_id))
