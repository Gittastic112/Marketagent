"""Authenticated adapter reads with original-response preservation and owned runs.

These workflows do not mutate current quotes, accepted identity, or holdings.
The existing ingestion service remains the transaction owner for price writes.
"""
import asyncio
from datetime import datetime, timezone
import hashlib

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.processing_run import ProcessingRun
from app.models.raw_document import RawDocument
from app.models.source import Source
from app.providers.calendars.exchange_calendar import get_exchange_schedule
from app.providers.identity.openfigi import OpenFIGIProvider
from app.providers.market_data.transport import canonical_json, provider_error
from app.schemas.data_adapters import DataAdapterReceipt
from app.services.market_data.base import MarketDataProviderError
from app.services.market_data.factory import get_market_data_provider
from app.services.processing_runs import start_processing_run


def _preserve(db: Session, provider: str, captures) -> tuple[list[int], int]:
    if not captures:
        return [], 0
    source_name = f"Official {provider} adapter responses"
    source = db.scalar(select(Source).where(Source.name == source_name))
    if source is None:
        try:
            with db.begin_nested():
                source = Source(name=source_name, source_type="official_market_api", base_url=captures[0].endpoint)
                db.add(source)
                db.flush()
        except IntegrityError:
            source = db.scalar(select(Source).where(Source.name == source_name))
            if source is None:
                raise
    ids, created = [], 0
    for capture in captures:
        identity = canonical_json({"provider": provider, "endpoint": capture.endpoint,
            "request": capture.request, "response_sha256": capture.sha256})
        digest = hashlib.sha256(identity.encode()).hexdigest()
        document = db.scalar(select(RawDocument).where(RawDocument.content_hash == digest))
        if document is None:
            try:
                with db.begin_nested():
                    document = RawDocument(source_id=source.id, document_type="market_data_response",
                        title=f"{provider} public response", url=capture.endpoint, published_at=None,
                        ingested_at=capture.observed_at, raw_text=capture.raw_text,
                        raw_payload_json={"provider": provider, "endpoint": capture.endpoint, "request": capture.request,
                            "response": capture.payload, "response_sha256": capture.sha256,
                            "observed_at": capture.observed_at.isoformat(), "publication_time": None,
                            "adapter_contract_version": 1}, content_hash=digest)
                    db.add(document)
                    db.flush()
                    created += 1
            except IntegrityError:
                document = db.scalar(select(RawDocument).where(RawDocument.content_hash == digest))
                if document is None:
                    raise
        ids.append(document.id)
    return list(dict.fromkeys(ids)), created


async def execute_data_adapter(db: Session, *, user_id: str, provider: str, operation: str,
                               request: BaseModel) -> DataAdapterReceipt:
    if not user_id:
        raise ValueError("An authenticated owner is required")
    run = start_processing_run(db, run_type="data_adapter_" + operation, source_type=provider,
        metadata={"user_id": user_id, "provider": provider, "operation": operation,
            "requested_scope": request.model_dump(mode="json"), "adapter_contract_version": 1,
            "request_budget": 32, "wall_time_budget_seconds": 120})
    run_id = run.id
    adapter = None
    try:
        async with asyncio.timeout(120):
            if provider == "openfigi" and operation == "identity":
                adapter = OpenFIGIProvider(api_key=getattr(get_settings(), "openfigi_api_key", None))
                result = await adapter.map_identity(request)
            elif provider == "exchange_calendar" and operation == "calendar":
                result = await asyncio.to_thread(get_exchange_schedule, request)
            else:
                adapter = get_market_data_provider(provider)
                method_name = {"quote": "get_quote", "history": "get_history", "dated_quote": "get_dated_quote",
                    "corporate_actions": "get_actions", "reference": "get_reference"}.get(operation)
                method = getattr(adapter, method_name, None) if method_name else None
                if method is None:
                    raise provider_error(provider, "PROVIDER_CAPABILITY_UNSUPPORTED",
                        "The selected adapter does not implement this capability.", status=422)
                result = await method(request)
        captures = getattr(adapter, "captures", [])
        ids, created = _preserve(db, provider, captures)
        snapshot = result.model_dump(mode="json")
        warnings = list(getattr(result, "warnings", []))
        gaps = list(getattr(result, "gaps", []))
        run.status = "partial_success" if getattr(result, "coverage", None) == "partial" else "success"
        run.fetched_count = len(captures) if adapter is not None else len(result.sessions)
        run.created_count = created
        run.skipped_duplicate_count = len(captures) - created
        run.error_count = len(gaps)
        run.error_details_json = {"codes": [g.code for g in gaps]} if gaps else None
        run.finished_at = datetime.now(timezone.utc)
        run.metadata_json = {**run.metadata_json, "source_document_ids": ids,
            "result_snapshot": snapshot, "result_sha256": hashlib.sha256(canonical_json(snapshot).encode()).hexdigest(),
            "outbound_request_count": getattr(getattr(adapter, "transport", None), "request_count", 0),
            "publication_time_policy": "unknown unless explicitly supplied; local observation is never backdated"}
        db.commit()
        return DataAdapterReceipt(provider=provider, observed_at=run.finished_at, processing_run_id=run.id,
            source_document_ids=ids, result=result, warnings=warnings)
    except (Exception, asyncio.CancelledError) as exc:
        db.rollback()
        if isinstance(exc, MarketDataProviderError):
            failure = exc
        elif isinstance(exc, (asyncio.CancelledError, TimeoutError)):
            failure = provider_error(provider, "ADAPTER_CANCELLED" if isinstance(exc, asyncio.CancelledError) else "ADAPTER_TIMEOUT",
                "Adapter operation was cancelled or exceeded its processing limit.", status=504, retryable=True)
        else:
            failure = provider_error(provider, "ADAPTER_FAILED", "Adapter operation could not be completed.")
        run = db.get(ProcessingRun, run_id)
        run.status = "failed"
        run.error_count = 1
        run.finished_at = datetime.now(timezone.utc)
        run.error_details_json = {"code": failure.code, "retryable": failure.retryable}
        run.fetched_count = run.created_count = run.skipped_duplicate_count = 0
        db.commit()
        if isinstance(exc, asyncio.CancelledError):
            raise
        failure.processing_run_id = run_id
        raise failure from None
