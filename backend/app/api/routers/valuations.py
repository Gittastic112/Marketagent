from typing import Sequence, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

import app.api.schemas as schemas
from app.api.dependencies import get_current_user
from app.api.errors import PublicApiError
from app.db.session import get_db
from app.models.company import Company
from app.models.dcf import ValuationModel, DcfAssumptionSet, DcfOutput, DcfProjectionYear, DcfSensitivityTable
from app.services.dcf import calculate_dcf
from app.services.reverse_dcf_engine import MarketImpliedAssumptionSolver
from app.services.industry_mapping import IndustryMappingService
from app.services.industry_assumption import IndustryAssumptionService
from app.services.valuation_context import build_company_valuation_context
from app.services.valuation_setup_draft import ValuationSetupDraftService
from app.services.quick_valuation import (
    calculate_quick_valuation,
    generate_quick_valuation_assumptions,
)
from app.api.schemas import ApiResponse

router = APIRouter(prefix="", tags=["valuations"])


@router.post(
    "/api/valuation/quick/assumptions",
    response_model=ApiResponse[schemas.QuickValuationAssumptionsRead],
)
def get_quick_valuation_assumptions(
    payload: schemas.QuickValuationAssumptionsRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[dict[str, Any]]:
    company = db.get(Company, payload.company_id)
    if company is None:
        raise PublicApiError(
            status_code=404,
            code="QUICK_VALUATION_COMPANY_NOT_FOUND",
            message="The selected company was not found.",
        )
    return ApiResponse(data=generate_quick_valuation_assumptions(db, company))


@router.post(
    "/api/valuation/quick/calculate",
    response_model=ApiResponse[schemas.QuickValuationOutputRead],
)
def run_quick_valuation(
    payload: schemas.QuickValuationCalculateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> ApiResponse[dict[str, Any]]:
    company = db.get(Company, payload.company_id)
    if company is None:
        raise PublicApiError(
            status_code=404,
            code="QUICK_VALUATION_COMPANY_NOT_FOUND",
            message="The selected company was not found.",
        )
    return ApiResponse(
        data=calculate_quick_valuation(company, payload),
        meta=schemas.ApiMeta(
            source="deterministic_fcff_dcf",
            confidence="medium",
            warnings=["Quick valuation outputs are calculations from reviewed or user-entered assumptions and are not persisted."],
        ),
    )


def get_owned_valuation_model(db: Session, model_id: int, user_id: str) -> ValuationModel:
    model = db.scalar(
        select(ValuationModel).where(
            ValuationModel.id == model_id,
            ValuationModel.user_id == user_id,
        )
    )
    if model is None:
        raise HTTPException(status_code=404, detail="Valuation model not found")
    return model


def get_owned_assumption_set(
    db: Session,
    model_id: int,
    assumption_id: int,
    user_id: str,
) -> DcfAssumptionSet:
    get_owned_valuation_model(db, model_id, user_id)
    assumption_set = db.scalar(
        select(DcfAssumptionSet).where(
            DcfAssumptionSet.id == assumption_id,
            DcfAssumptionSet.valuation_model_id == model_id,
        )
    )
    if assumption_set is None:
        raise HTTPException(status_code=404, detail="Assumption set not found")
    return assumption_set


def get_owned_assumption_set_by_id(
    db: Session,
    assumption_id: int,
    user_id: str,
) -> DcfAssumptionSet:
    assumption_set = db.scalar(
        select(DcfAssumptionSet)
        .join(ValuationModel, DcfAssumptionSet.valuation_model_id == ValuationModel.id)
        .where(
            DcfAssumptionSet.id == assumption_id,
            ValuationModel.user_id == user_id,
        )
    )
    if assumption_set is None:
        raise HTTPException(status_code=404, detail="Assumption set not found")
    return assumption_set


@router.get("/api/valuation/context/company/{company_id}", response_model=ApiResponse[schemas.ValuationCompanyContextRead])
def get_company_valuation_context(company_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return ApiResponse(data=build_company_valuation_context(company))


@router.post("/companies/{company_id}/valuation-models", response_model=ApiResponse[schemas.ValuationModelRead], status_code=status.HTTP_201_CREATED)
def create_valuation_model(company_id: int, model_in: schemas.ValuationModelCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> Any:
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    vmodel = ValuationModel(**model_in.model_dump(), user_id=current_user["id"])
    vmodel.company_id = company_id
    db.add(vmodel)
    db.commit()
    db.refresh(vmodel)
    return ApiResponse(data=vmodel)


@router.get("/companies/{company_id}/valuation-models", response_model=ApiResponse[list[schemas.ValuationModelRead]])
def list_valuation_models(company_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> Any:
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    models = db.scalars(
        select(ValuationModel).where(ValuationModel.user_id == current_user["id"])
        .where(ValuationModel.company_id == company_id)
        .order_by(ValuationModel.created_at.desc())
    ).all()
    return ApiResponse(data=models)


@router.post("/valuation-models/{model_id}/assumptions", response_model=ApiResponse[schemas.DcfAssumptionSetRead], status_code=status.HTTP_201_CREATED)
def create_dcf_assumption_set(model_id: int, assumption_in: schemas.DcfAssumptionSetCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> Any:
    vmodel = get_owned_valuation_model(db, model_id, current_user["id"])

    aset = DcfAssumptionSet(**assumption_in.model_dump())
    aset.valuation_model_id = model_id
    db.add(aset)
    db.commit()
    db.refresh(aset)

    # Immediately calculate and store output
    output, projection_years, sensitivity_tables = calculate_dcf(aset, model_type=vmodel.model_type)
    db.add(output)
    db.add_all(projection_years)
    db.add_all(sensitivity_tables)
    db.commit()
    db.refresh(aset)

    # Generate assumption diffs
    from app.services.assumption_diff_service import AssumptionDiffService
    AssumptionDiffService.generate_change_logs(db, aset)
    db.refresh(aset)

    return ApiResponse(data=aset)


@router.get("/valuation-models/{model_id}/assumptions", response_model=ApiResponse[list[schemas.DcfAssumptionSetRead]])
def list_dcf_assumption_sets(model_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> Sequence[DcfAssumptionSet]:
    get_owned_valuation_model(db, model_id, current_user["id"])

    asets = db.scalars(
        select(DcfAssumptionSet)
        .where(DcfAssumptionSet.valuation_model_id == model_id)
        .order_by(DcfAssumptionSet.created_at.desc())
    ).all()
    return ApiResponse(data=asets)


@router.delete("/valuation-models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_valuation_model(model_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> None:
    vmodel = get_owned_valuation_model(db, model_id, current_user["id"])

    db.delete(vmodel)
    db.commit()


@router.get("/valuation-models/{model_id}/assumptions/{assumption_id}/forecast", response_model=ApiResponse[list[schemas.DcfProjectionYearRead]])
def get_dcf_forecast(model_id: int, assumption_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> Sequence[schemas.DcfProjectionYearRead]:
    aset = get_owned_assumption_set(db, model_id, assumption_id, current_user["id"])
    return ApiResponse(data=aset.projection_years)


@router.get("/valuation-models/{model_id}/assumptions/{assumption_id}/results", response_model=ApiResponse[schemas.DcfOutputRead])
def get_dcf_results(model_id: int, assumption_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> schemas.DcfOutputRead:
    aset = get_owned_assumption_set(db, model_id, assumption_id, current_user["id"])

    if not aset.outputs:
        raise HTTPException(status_code=404, detail="Results not found")

    return ApiResponse(data=aset.outputs)


@router.get("/valuation-models/{model_id}/assumptions/{assumption_id}/sensitivity", response_model=ApiResponse[list[schemas.DcfSensitivityTableRead]])
def get_dcf_sensitivity(model_id: int, assumption_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> Sequence[schemas.DcfSensitivityTableRead]:
    aset = get_owned_assumption_set(db, model_id, assumption_id, current_user["id"])
    return ApiResponse(data=aset.sensitivity_tables)


@router.get("/valuation-models/{model_id}/assumptions/{assumption_id}/scenarios", response_model=ApiResponse[list[schemas.DcfScenarioOutput]])
def get_dcf_scenarios(model_id: int, assumption_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> Sequence[schemas.DcfScenarioOutput]:
    aset = get_owned_assumption_set(db, model_id, assumption_id, current_user["id"])

    from app.services.scenario_engine import ScenarioEngine
    scenarios = ScenarioEngine.run_scenarios(aset)
    return ApiResponse(data=scenarios)


@router.post("/dcf/reverse", response_model=ApiResponse[schemas.ReverseDcfResponse])
def solve_reverse_dcf(request: schemas.ReverseDcfRequest, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> ApiResponse[schemas.ReverseDcfResponse]:
    aset = get_owned_assumption_set_by_id(db, request.assumption_set_id, current_user["id"])

    diluted_shares = request.diluted_shares or aset.diluted_shares or 1.0

    implied_value, original_value, diagnostics = MarketImpliedAssumptionSolver.solve(
        assumption_set=aset,
        target_parameter=request.target_parameter,
        current_market_price=request.current_market_price,
        diluted_shares=diluted_shares
    )

    return ApiResponse(data=schemas.ReverseDcfResponse(
        target_parameter=request.target_parameter,
        implied_value=implied_value,
        original_value=original_value,
        intrinsic_value_at_implied=request.current_market_price if implied_value is not None else None,
        diagnostics=diagnostics
    ))

@router.get("/industries/suggest", response_model=ApiResponse[list[dict[str, Any]]])
def suggest_industries(companyId: int, country: str = "India", db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    candidates = IndustryMappingService.suggest_damodaran_industries(db, companyId, country)
    return ApiResponse(data=candidates)

@router.get("/assumption-priors", response_model=ApiResponse[dict[str, Any]])
def get_assumption_priors(country: str, industry: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    priors = IndustryAssumptionService.get_assumption_priors(db, country, industry)
    return ApiResponse(data=priors)

@router.post("/valuation-models/{model_id}/assumptions/{assumption_id}/resolve-stale", response_model=ApiResponse[schemas.DcfAssumptionSetRead])
def resolve_stale_valuation(model_id: int, assumption_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> schemas.DcfAssumptionSetRead:
    aset = get_owned_assumption_set(db, model_id, assumption_id, current_user["id"])

    aset.is_stale = False
    aset.stale_reason = None
    aset.stale_event_id = None
    db.commit()
    db.refresh(aset)
    return ApiResponse(data=aset)

@router.get("/valuation-models/{model_id}/assumptions/{assumption_id}/change-logs", response_model=ApiResponse[list[schemas.ValuationAssumptionChangeLogRead]])
def list_change_logs(model_id: int, assumption_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> Sequence[schemas.ValuationAssumptionChangeLogRead]:
    aset = get_owned_assumption_set(db, model_id, assumption_id, current_user["id"])
    return ApiResponse(data=aset.change_logs)

@router.post("/valuation-models/{model_id}/assumptions/{assumption_id}/change-logs", response_model=ApiResponse[schemas.ValuationAssumptionChangeLogRead], status_code=status.HTTP_201_CREATED)
def create_change_log(model_id: int, assumption_id: int, payload: schemas.ValuationAssumptionChangeLogCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)) -> schemas.ValuationAssumptionChangeLogRead:
    from app.models.dcf import ValuationAssumptionChangeLog
    aset = get_owned_assumption_set(db, model_id, assumption_id, current_user["id"])

    change_log_data = payload.model_dump()
    change_log_data["valuation_model_id"] = model_id
    change_log_data["assumption_set_id"] = assumption_id
    change_log = ValuationAssumptionChangeLog(**change_log_data)
    db.add(change_log)

    # Phase 13 logic: Mark the underlying assumption set as stale since an event altered assumptions
    if payload.event_id:
        aset.is_stale = True
        aset.stale_reason = f"Event triggered review of {payload.parameter_name}"
        aset.stale_event_id = payload.event_id

    db.commit()
    db.refresh(change_log)
    return ApiResponse(data=change_log)

@router.get("/valuation-models/{model_id}/assumptions/{assumption_id}/diagnostics", response_model=ApiResponse[list[schemas.DiagnosticWarning]])
def get_diagnostics(model_id: int, assumption_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    aset = get_owned_assumption_set(db, model_id, assumption_id, current_user["id"])

    if aset.outputs and aset.outputs.warnings_json:
        return ApiResponse(data=[schemas.DiagnosticWarning(**w) for w in aset.outputs.warnings_json])
    return ApiResponse(data=[])

@router.post(
    "/companies/{company_id}/valuation-models/autofill",
    response_model=ApiResponse[dict[str, Any]],
)
def autofill_assumptions(company_id: int, payload: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    from app.services.assumption_autofill_engine import AssumptionAutofillEngine
    base_assumptions = payload.get("base_assumptions", {})
    try:
        draft = AssumptionAutofillEngine.draft_assumptions(db, company_id, base_assumptions)
        return ApiResponse(data=draft)
    except ValueError as exc:
        raise PublicApiError(
            status_code=404,
            code="VALUATION_AUTOFILL_INPUT_NOT_FOUND",
            message="Company or valuation autofill inputs were not found.",
        ) from exc


@router.post(
    "/companies/{company_id}/valuation-drafts",
    response_model=ApiResponse[schemas.ValuationSetupDraftRead],
    status_code=status.HTTP_201_CREATED,
)
def create_or_reopen_valuation_draft(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    draft = ValuationSetupDraftService.create_or_reopen(db, company_id, current_user["id"])
    return ApiResponse(data=draft)


@router.get(
    "/valuation-drafts/{draft_id}",
    response_model=ApiResponse[schemas.ValuationSetupDraftRead],
)
def get_valuation_draft(
    draft_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ApiResponse(data=ValuationSetupDraftService.get_owned(db, draft_id, current_user["id"]))


@router.patch(
    "/valuation-drafts/{draft_id}",
    response_model=ApiResponse[schemas.ValuationSetupDraftRead],
)
def update_valuation_draft(
    draft_id: int,
    payload: schemas.ValuationSetupDraftUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    draft = ValuationSetupDraftService.get_owned(db, draft_id, current_user["id"])
    return ApiResponse(
        data=ValuationSetupDraftService.update(
            db,
            draft,
            payload.assumptions_patch,
            payload.reviewed_fields,
            payload.expected_updated_at,
        )
    )


@router.post(
    "/valuation-drafts/{draft_id}/refresh",
    response_model=ApiResponse[schemas.ValuationSetupDraftRead],
)
def refresh_valuation_draft(
    draft_id: int,
    payload: schemas.ValuationSetupDraftCommand,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    draft = ValuationSetupDraftService.get_owned(db, draft_id, current_user["id"])
    return ApiResponse(
        data=ValuationSetupDraftService.refresh(db, draft, payload.expected_updated_at)
    )


@router.post(
    "/valuation-drafts/{draft_id}/reset",
    response_model=ApiResponse[schemas.ValuationSetupDraftRead],
)
def reset_valuation_draft_fields(
    draft_id: int,
    payload: schemas.ValuationSetupDraftReset,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    draft = ValuationSetupDraftService.get_owned(db, draft_id, current_user["id"])
    return ApiResponse(
        data=ValuationSetupDraftService.reset_fields(
            db,
            draft,
            payload.fields,
            payload.expected_updated_at,
        )
    )


@router.post(
    "/valuation-drafts/{draft_id}/archive",
    response_model=ApiResponse[schemas.ValuationSetupDraftRead],
)
def archive_valuation_draft(
    draft_id: int,
    payload: schemas.ValuationSetupDraftCommand,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    draft = ValuationSetupDraftService.get_owned(db, draft_id, current_user["id"])
    return ApiResponse(
        data=ValuationSetupDraftService.archive(db, draft, payload.expected_updated_at)
    )


@router.post(
    "/valuation-drafts/{draft_id}/promote",
    response_model=ApiResponse[schemas.ValuationModelRead],
    status_code=status.HTTP_201_CREATED,
)
def promote_valuation_draft(
    draft_id: int,
    payload: schemas.ValuationSetupDraftPromote,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    draft = ValuationSetupDraftService.get_owned(db, draft_id, current_user["id"])
    model = ValuationSetupDraftService.promote(
        db,
        draft,
        payload.name,
        payload.description,
        payload.model_type,
        payload.expected_updated_at,
    )
    return ApiResponse(data=model)
