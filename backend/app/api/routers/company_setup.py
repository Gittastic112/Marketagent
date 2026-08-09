from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.schemas import (
    ApiResponse,
    CompanySetupIdentityResolution,
    CompanySetupStartRequest,
    CompanySetupStepUpdate,
    CompanySetupWorkflowRead,
)
from app.db.session import get_db
from app.services.company_setup import (
    confirm_company_identity,
    get_company_setup,
    get_or_start_company_setup,
    resolve_company_identity,
    update_company_setup_step,
)


router = APIRouter(prefix="/api/company-setup", tags=["company_setup"])


@router.post("/start", response_model=ApiResponse[CompanySetupWorkflowRead], status_code=status.HTTP_201_CREATED)
def start_company_setup(payload: CompanySetupStartRequest, db: Session = Depends(get_db)) -> ApiResponse[CompanySetupWorkflowRead]:
    return ApiResponse(data=get_or_start_company_setup(db, payload.company_id))


@router.get("/{company_id}", response_model=ApiResponse[CompanySetupWorkflowRead])
def read_company_setup(company_id: int, db: Session = Depends(get_db)) -> ApiResponse[CompanySetupWorkflowRead]:
    return ApiResponse(data=get_company_setup(db, company_id))


@router.patch("/{company_id}/step", response_model=ApiResponse[CompanySetupWorkflowRead])
def update_company_setup(company_id: int, payload: CompanySetupStepUpdate, db: Session = Depends(get_db)) -> ApiResponse[CompanySetupWorkflowRead]:
    return ApiResponse(data=update_company_setup_step(db, company_id, payload))


@router.post("/{company_id}/resolve-identity", response_model=ApiResponse[CompanySetupIdentityResolution])
def resolve_identity(company_id: int, db: Session = Depends(get_db)) -> ApiResponse[CompanySetupIdentityResolution]:
    return ApiResponse(data=resolve_company_identity(db, company_id))


@router.post("/{company_id}/confirm-identity", response_model=ApiResponse[CompanySetupWorkflowRead])
def confirm_identity(company_id: int, db: Session = Depends(get_db)) -> ApiResponse[CompanySetupWorkflowRead]:
    return ApiResponse(data=confirm_company_identity(db, company_id))
