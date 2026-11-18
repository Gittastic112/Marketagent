"""Explicit, authenticated official-source adapter actions; no implicit fetch on reads."""
from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.errors import PublicApiError
from app.db.session import get_db
from app.schemas.common import ApiMeta, ApiResponse
from app.schemas.data_adapters import (AdapterActionRequest, AdapterActionsResult, AdapterDatedQuoteRequest,
    AdapterDatedQuoteResult, AdapterHistoryRequest, AdapterHistoryResult, CalendarScheduleRequest,
    CalendarScheduleResult, DataAdapterReceipt, IdentityMappingRequest, IdentityMappingResult,
    MarketDataRequest, MarketQuoteResult, SecurityReferenceResult)
from app.services.market_data.adapter_workflow import execute_data_adapter
from app.services.market_data.base import MarketDataProviderError

router = APIRouter(prefix="/api/data-adapters", tags=["data-adapters"], dependencies=[Depends(get_current_user)])
OfficialProvider = Literal["fmp", "massive", "nse_mcp"]


async def _execute(db, user, provider, operation, payload):
    try:
        receipt = await execute_data_adapter(db, user_id=user["id"], provider=provider, operation=operation, request=payload)
    except MarketDataProviderError as exc:
        raise PublicApiError(status_code=exc.status_code, code=exc.code, message=exc.message,
            retryable=exc.retryable, provider=exc.provider, processing_run_id=exc.processing_run_id) from None
    coverage = getattr(receipt.result, "coverage", None)
    status = "partial" if coverage == "partial" else "empty" if coverage == "empty" else "success"
    source_time = getattr(receipt.result, "source_timestamp", None)
    stale = bool(source_time and receipt.observed_at - source_time > timedelta(minutes=20))
    warnings = list(receipt.warnings)
    if stale:
        warnings.append("Quote timestamp exceeds the 20-minute inspection freshness threshold; the market may be closed.")
    return ApiResponse(data=receipt, meta=ApiMeta(status=status, source=provider,
        last_updated=source_time or receipt.observed_at, is_stale=stale,
        warnings=warnings, confidence="medium"))


@router.post("/{provider}/quote", response_model=ApiResponse[DataAdapterReceipt[MarketQuoteResult]])
async def adapter_quote(provider: OfficialProvider, payload: MarketDataRequest,
    db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return await _execute(db, user, provider, "quote", payload)


@router.post("/{provider}/history", response_model=ApiResponse[DataAdapterReceipt[AdapterHistoryResult]])
async def adapter_history(provider: OfficialProvider, payload: AdapterHistoryRequest,
    db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return await _execute(db, user, provider, "history", payload)


@router.post("/{provider}/dated-quote", response_model=ApiResponse[DataAdapterReceipt[AdapterDatedQuoteResult]])
async def adapter_dated_quote(provider: OfficialProvider, payload: AdapterDatedQuoteRequest,
    db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return await _execute(db, user, provider, "dated_quote", payload)


@router.post("/{provider}/corporate-actions", response_model=ApiResponse[DataAdapterReceipt[AdapterActionsResult]])
async def adapter_actions(provider: OfficialProvider, payload: AdapterActionRequest,
    db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return await _execute(db, user, provider, "corporate_actions", payload)


@router.post("/{provider}/reference", response_model=ApiResponse[DataAdapterReceipt[SecurityReferenceResult]])
async def adapter_reference(provider: OfficialProvider, payload: MarketDataRequest,
    db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return await _execute(db, user, provider, "reference", payload)


@router.post("/identity/openfigi", response_model=ApiResponse[DataAdapterReceipt[IdentityMappingResult]])
async def adapter_identity(payload: IdentityMappingRequest, db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)):
    return await _execute(db, user, "openfigi", "identity", payload)


@router.post("/calendars/schedule", response_model=ApiResponse[DataAdapterReceipt[CalendarScheduleResult]])
async def adapter_calendar(payload: CalendarScheduleRequest, db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)):
    return await _execute(db, user, "exchange_calendar", "calendar", payload)
