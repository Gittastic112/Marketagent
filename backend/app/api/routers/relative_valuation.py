from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.services.relative_valuation import RelativeValuationBenchmarkService, RelativeValuationRunService, RelativeValuationRequest
from app.services.peer_valuation_sets import (
    PeerValuationSetCreate,
    PeerValuationSetMutation,
    PeerValuationSetReview,
    PeerValuationSetService,
    PeerValuationSetUpdate,
    peer_set_response,
)
from app.services.peer_valuation_import import (
    PeerCsvApplyRequest,
    PeerCsvPreviewRequest,
    apply_peer_csv,
    export_peer_csv,
    peer_csv_template,
    preview_peer_csv,
)
from app.schemas.common import ApiResponse
from app.services.relative_valuation import SavedRelativeValuationRequest
from app.services.saved_relative_inputs import load_saved_relative_inputs, saved_input_meta

router = APIRouter(prefix="/api/valuation/relative", tags=["relative-valuation"])
legacy_router = APIRouter(prefix="/relative-valuation", tags=["relative-valuation"])


@router.get("/assumptions/{assumption_id}/inputs", response_model=ApiResponse)
def get_saved_relative_inputs(
    assumption_id: int = Path(ge=1, le=2_147_483_647),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    basis = load_saved_relative_inputs(db, assumption_id=assumption_id, user_id=current_user["id"])
    return ApiResponse(data=basis, meta=saved_input_meta(basis))


@router.post("/assumptions/{assumption_id}/run", response_model=ApiResponse)
def run_saved_relative_valuation(
    payload: SavedRelativeValuationRequest,
    assumption_id: int = Path(ge=1, le=2_147_483_647),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    basis = load_saved_relative_inputs(db, assumption_id=assumption_id, user_id=current_user["id"])
    if not payload.confirmInputBasis:
        raise HTTPException(status_code=422, detail="Confirm the saved input basis, consistent currency/scale, and simplified equity bridge.")
    if payload.inputBasisSha256 != basis["inputBasisSha256"]:
        raise HTTPException(status_code=409, detail="Saved input basis changed. Refresh and review it before calculating.")
    if not basis["canCalculate"]:
        raise HTTPException(status_code=422, detail=" ".join(basis["blockers"]))
    request = RelativeValuationRequest(**payload.model_dump(exclude={"confirmInputBasis", "inputBasisSha256"}),
        companyId=str(basis["companyId"]), financials=basis["financials"])
    result = RelativeValuationRunService.run_valuation(db, request, user_id=current_user["id"])
    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])
    result["inputBasis"] = basis
    return ApiResponse(data=result, meta=saved_input_meta(basis))


def _meta() -> dict[str, Any]:
    return {
        "source": "Damodaran India pricing workbooks",
        "confidence": "high",
        "is_mock": False,
    }


def _country_stats_meta() -> dict[str, Any]:
    return {
        "source": "Damodaran country statistics",
        "confidence": "high",
        "is_mock": False,
        "warnings": [],
    }


def _peer_set_meta() -> dict[str, Any]:
    return {
        "source": "user_reviewed_peer_evidence",
        "confidence": "medium",
        "is_mock": False,
        "warnings": ["Peer multiples remain user-supplied facts or source summaries until reviewed."],
    }


@router.get("/peer-sets", response_model=ApiResponse)
def list_peer_valuation_sets(
    company_id: int | None = Query(default=None, ge=1),
    include_archived: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ApiResponse(
        data=PeerValuationSetService.list_sets(
            db,
            user_id=current_user["id"],
            company_id=company_id,
            include_archived=include_archived,
        ),
        meta=_peer_set_meta(),
    )


@router.post("/peer-sets", response_model=ApiResponse)
def create_peer_valuation_set(
    payload: PeerValuationSetCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    peer_set = PeerValuationSetService.create_set(
        db,
        user_id=current_user["id"],
        payload=payload,
    )
    return ApiResponse(data=peer_set_response(peer_set), meta=_peer_set_meta())


@router.get("/peer-sets/import/template", response_model=ApiResponse)
def get_peer_valuation_csv_template(
    current_user: dict = Depends(get_current_user),
):
    del current_user
    return ApiResponse(data=peer_csv_template(), meta=_peer_set_meta())


@router.post("/peer-sets/import/preview", response_model=ApiResponse)
def preview_peer_valuation_csv(
    payload: PeerCsvPreviewRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    del current_user
    return ApiResponse(data=preview_peer_csv(db, payload=payload), meta=_peer_set_meta())


@router.post("/peer-sets/import/apply", response_model=ApiResponse)
def apply_peer_valuation_csv(
    payload: PeerCsvApplyRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ApiResponse(
        data=apply_peer_csv(db, user_id=current_user["id"], payload=payload),
        meta=_peer_set_meta(),
    )


@router.get("/peer-sets/{peer_set_id}", response_model=ApiResponse)
def get_peer_valuation_set(
    peer_set_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    peer_set = PeerValuationSetService.get_set(
        db,
        peer_set_id=peer_set_id,
        user_id=current_user["id"],
    )
    return ApiResponse(data=peer_set_response(peer_set), meta=_peer_set_meta())


@router.put("/peer-sets/{peer_set_id}", response_model=ApiResponse)
def update_peer_valuation_set(
    peer_set_id: int,
    payload: PeerValuationSetUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    peer_set = PeerValuationSetService.update_set(
        db,
        peer_set_id=peer_set_id,
        user_id=current_user["id"],
        payload=payload,
    )
    return ApiResponse(data=peer_set_response(peer_set), meta=_peer_set_meta())


@router.post("/peer-sets/{peer_set_id}/review", response_model=ApiResponse)
def review_peer_valuation_set(
    peer_set_id: int,
    payload: PeerValuationSetReview,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    peer_set = PeerValuationSetService.review_set(
        db,
        peer_set_id=peer_set_id,
        user_id=current_user["id"],
        payload=payload,
    )
    return ApiResponse(data=peer_set_response(peer_set), meta=_peer_set_meta())


@router.get("/peer-sets/{peer_set_id}/revisions", response_model=ApiResponse)
def list_peer_valuation_set_revisions(
    peer_set_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return ApiResponse(
        data=PeerValuationSetService.list_revisions(
            db,
            peer_set_id=peer_set_id,
            user_id=current_user["id"],
        ),
        meta=_peer_set_meta(),
    )


@router.get("/peer-sets/{peer_set_id}/export", response_model=ApiResponse)
def export_peer_valuation_set(
    peer_set_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    peer_set = PeerValuationSetService.get_set(
        db,
        peer_set_id=peer_set_id,
        user_id=current_user["id"],
    )
    return ApiResponse(
        data=export_peer_csv(peer_set_response(peer_set)),
        meta=_peer_set_meta(),
    )


@router.post("/peer-sets/{peer_set_id}/restore", response_model=ApiResponse)
def restore_peer_valuation_set(
    peer_set_id: int,
    payload: PeerValuationSetMutation,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    peer_set = PeerValuationSetService.restore_set(
        db,
        peer_set_id=peer_set_id,
        user_id=current_user["id"],
        payload=payload,
    )
    return ApiResponse(data=peer_set_response(peer_set), meta=_peer_set_meta())


@router.delete("/peer-sets/{peer_set_id}", response_model=ApiResponse)
def archive_peer_valuation_set(
    peer_set_id: int,
    expected_version: int = Query(ge=1),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    peer_set = PeerValuationSetService.archive_set(
        db,
        peer_set_id=peer_set_id,
        user_id=current_user["id"],
        expected_version=expected_version,
    )
    return ApiResponse(data=peer_set_response(peer_set), meta=_peer_set_meta())

@legacy_router.get("/countries", response_model=ApiResponse, include_in_schema=False)
@router.get("/countries", response_model=ApiResponse)
def get_countries(db: Session = Depends(get_db)):
    countries = RelativeValuationBenchmarkService.get_countries(db)
    return ApiResponse(data=countries, meta=_meta())

@legacy_router.get("/countries/{country}/stats", response_model=ApiResponse, include_in_schema=False)
@router.get("/countries/{country}/stats", response_model=ApiResponse)
def get_country_stats(country: str, db: Session = Depends(get_db)):
    stats = RelativeValuationBenchmarkService.get_country_stats(db, country)
    if not stats:
        return ApiResponse(
            data=None,
            meta={**_country_stats_meta(), "status": "error"},
            errors=[{"code": "NOT_FOUND", "message": f"Stats not found for country {country}"}],
        )
    return ApiResponse(data=stats.as_dict(), meta=_country_stats_meta())

@legacy_router.get("/countries/{country}/industries", response_model=ApiResponse, include_in_schema=False)
@router.get("/countries/{country}/industries", response_model=ApiResponse)
def get_industries(country: str, db: Session = Depends(get_db)):
    industries = RelativeValuationBenchmarkService.get_industries(db, country)
    return ApiResponse(data=industries, meta=_meta())

@legacy_router.get("/countries/{country}/industries/{industry}", response_model=ApiResponse, include_in_schema=False)
@router.get("/countries/{country}/industries/{industry}", response_model=ApiResponse)
def get_industry_benchmark(country: str, industry: str, db: Session = Depends(get_db)):
    benchmark = RelativeValuationBenchmarkService.get_industry_benchmark(db, country, industry)
    if not benchmark:
        return ApiResponse(
            data=None,
            meta={"status": "error"},
            errors=[{"code": "NOT_FOUND", "message": f"Benchmark not found for {industry} in {country}"}],
        )
    return ApiResponse(data=benchmark.as_dict(), meta=_meta())

@legacy_router.post("/run", response_model=ApiResponse, include_in_schema=False)
@router.post("/run", response_model=ApiResponse)
def run_relative_valuation(
    request: RelativeValuationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = RelativeValuationRunService.run_valuation(
        db,
        request,
        user_id=current_user["id"],
    )
    response_meta = _peer_set_meta() if request.peerSetId is not None else _meta()
    if "error" in result:
        return ApiResponse(
            data=None,
            meta={"status": "error"},
            errors=[{"code": "VALUATION_ERROR", "message": result["error"]}],
        )
    return ApiResponse(data=result, meta=response_meta)
