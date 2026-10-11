"""One audited transaction boundary for quote-only and quote/history ingestion."""
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.market_price import MarketPrice
from app.models.processing_run import ProcessingRun
from app.services.market_data.base import MarketDataProviderError
from app.services.market_data.factory import get_market_data_provider
from app.services.market_data.persistence import persist_history_point, persist_quote, request_for_company
from app.services.valuation_alert_service import check_price_valuation_divergence


@dataclass(frozen=True)
class MarketIngestionResult:
    market_price: MarketPrice
    provider: str
    fetched_count: int
    created_count: int
    skipped_duplicate_count: int
    processing_run_id: int


async def ingest_company_prices(
    db: Session, *, company: Company, user_id: str, days: int = 365,
    include_history: bool = True,
) -> MarketIngestionResult:
    if not user_id or not 1 <= days <= 3650:
        raise ValueError("An owner and a history window of 1-3650 days are required")
    run = ProcessingRun(
        run_type="market_data_ingestion" if include_history else "market_quote_ingestion",
        company_id=company.id, started_at=datetime.now(timezone.utc), status="running",
        metadata_json={"days": days if include_history else None, "user_id": user_id},
    )
    db.add(run)
    db.commit()
    run_id = run.id
    provider_name = "unconfigured"
    try:
        provider = get_market_data_provider()
        provider_name = provider.provider_name
        run.source_type = provider_name
        run.metadata_json = {**run.metadata_json, "provider": provider_name}
        request = request_for_company(company)
        quote = await provider.get_quote(request)
        history = await provider.get_historical_prices(request, days=days) if include_history else []
        market_price, _, created = persist_quote(db, company=company, quote=quote)
        created_count = int(created)
        duplicate_count = int(not created)
        # Autoflush is off. Make each write visible to subsequent same-date lookups.
        db.flush()
        for point in history:
            _, created = persist_history_point(db, company=company, point=point)
            created_count += int(created)
            duplicate_count += int(not created)
            db.flush()
        check_price_valuation_divergence(db, company.id, user_id=user_id, commit=False)
        run.fetched_count = len(history) + 1
        run.created_count = created_count
        run.skipped_duplicate_count = duplicate_count
        run.status = "completed"
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(market_price)
        return MarketIngestionResult(market_price, provider_name, run.fetched_count,
            created_count, duplicate_count, run_id)
    except Exception as exc:
        db.rollback()
        run = db.get(ProcessingRun, run_id)
        if isinstance(exc, MarketDataProviderError):
            failure = exc
        else:
            failure = MarketDataProviderError(
                code="MARKET_DATA_INGESTION_FAILED", message="Market data ingestion failed.",
                provider=provider_name,
            )
        run.status = "failed"
        run.source_type = failure.provider
        run.error_count = 1
        run.fetched_count = run.created_count = run.skipped_duplicate_count = 0
        run.error_details_json = {"code": failure.code, "provider": failure.provider}
        run.finished_at = datetime.now(timezone.utc)
        db.commit()
        failure.processing_run_id = run_id
        raise failure from None
