from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api import schemas
from app.db.session import get_db
from app.models.company import Company
from app.models.dcf import ValuationModel, DcfAssumptionSet, DcfOutput
from app.services.dcf import calculate_dcf
from app.api.schemas import ApiResponse

router = APIRouter(prefix="", tags=["valuations"])


@router.post("/companies/{company_id}/valuation-models", response_model=ApiResponse[schemas.ValuationModelRead], status_code=status.HTTP_201_CREATED)
def create_valuation_model(company_id: int, model_in: schemas.ValuationModelCreate, db: Session = Depends(get_db)) -> ValuationModel:
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    vmodel = ValuationModel(**model_in.model_dump())
    vmodel.company_id = company_id
    db.add(vmodel)
    db.commit()
    db.refresh(vmodel)
    return ApiResponse(data=vmodel)


@router.get("/companies/{company_id}/valuation-models", response_model=ApiResponse[list[schemas.ValuationModelRead]])
def list_valuation_models(company_id: int, db: Session = Depends(get_db)) -> Sequence[ValuationModel]:
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    models = db.scalars(
        select(ValuationModel)
        .where(ValuationModel.company_id == company_id)
        .order_by(ValuationModel.created_at.desc())
    ).all()
    return ApiResponse(data=models)


@router.post("/valuation-models/{model_id}/assumptions", response_model=ApiResponse[schemas.DcfAssumptionSetRead], status_code=status.HTTP_201_CREATED)
def create_dcf_assumption_set(model_id: int, assumption_in: schemas.DcfAssumptionSetCreate, db: Session = Depends(get_db)) -> DcfAssumptionSet:
    vmodel = db.get(ValuationModel, model_id)
    if not vmodel:
        raise HTTPException(status_code=404, detail="Valuation model not found")

    aset = DcfAssumptionSet(**assumption_in.model_dump())
    aset.valuation_model_id = model_id
    db.add(aset)
    db.commit()
    db.refresh(aset)

    # Immediately calculate and store output
    output = calculate_dcf(aset)
    db.add(output)
    db.commit()
    db.refresh(aset)

    return ApiResponse(data=aset)


@router.get("/valuation-models/{model_id}/assumptions", response_model=ApiResponse[list[schemas.DcfAssumptionSetRead]])
def list_dcf_assumption_sets(model_id: int, db: Session = Depends(get_db)) -> Sequence[DcfAssumptionSet]:
    vmodel = db.get(ValuationModel, model_id)
    if not vmodel:
        raise HTTPException(status_code=404, detail="Valuation model not found")

    asets = db.scalars(
        select(DcfAssumptionSet)
        .where(DcfAssumptionSet.valuation_model_id == model_id)
        .order_by(DcfAssumptionSet.created_at.desc())
    ).all()
    return ApiResponse(data=asets)


@router.delete("/valuation-models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_valuation_model(model_id: int, db: Session = Depends(get_db)) -> None:
    vmodel = db.get(ValuationModel, model_id)
    if not vmodel:
        raise HTTPException(status_code=404, detail="Valuation model not found")
    
    db.delete(vmodel)
    db.commit()
