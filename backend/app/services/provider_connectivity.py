"""Explicit public-only probes. Success is connectivity, never stored coverage."""
import asyncio
from datetime import datetime, timezone
import time

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.processing_run import ProcessingRun
from app.providers.fred_provider import FredProvider
from app.services.market_data.base import MarketDataProviderError, MarketDataRequest
from app.services.market_data.factory import get_market_data_provider
from app.services.sec_ingestion import fetch_recent_sec_filing_metadata, lookup_cik_for_ticker


def probe_public_provider(db: Session, provider: str, *, request: MarketDataRequest | None = None) -> dict:
    if provider not in {"sec", "fred", "market"} or (provider in {"sec", "market"} and request is None):
        raise ValueError("Select SEC, FRED or market connectivity with an explicit public identity")
    if provider == "sec" and request.market != "US":
        raise ValueError("SEC identity probes require a US security")
    run = ProcessingRun(run_type="provider_connectivity_probe", source_type=provider,
        started_at=datetime.now(timezone.utc), status="running", metadata_json={
            "identity": request.model_dump() if request else None,
            "is_mock": False, "external_data_classes": ["public_security_identity"] if request else ["public_series_id"],
            "limitations": "Connectivity only. No company, price, financial or review records are created.",
        })
    db.add(run)
    db.commit()
    started = time.monotonic()
    evidence, code = {}, None
    try:
        settings = get_settings()
        if provider == "sec":
            cik = lookup_cik_for_ticker(request.ticker, user_agent=settings.sec_user_agent)
            filings = fetch_recent_sec_filing_metadata(cik, user_agent=settings.sec_user_agent)
            evidence = {"cik": cik, "filing_count": len(filings), "source": "https://www.sec.gov/files/company_tickers.json"}
        elif provider == "fred":
            if not settings.fred_api_key:
                raise MarketDataProviderError(code="PROVIDER_NOT_CONFIGURED", provider="FRED", message="Not configured")
            observations = FredProvider(settings.fred_api_key).fetch_observations("DGS10", limit=1)
            if not observations or not observations[0].get("date"):
                raise ValueError("Missing observation")
            evidence = {"series_id": "DGS10", "latest_observation_date": observations[0]["date"],
                "source": "https://fred.stlouisfed.org/series/DGS10"}
        else:
            selected = get_market_data_provider()
            async def prices():
                quote = await selected.get_quote(request)
                history = await selected.get_historical_prices(request, days=7)
                if (quote.ticker != request.ticker or quote.market != request.market
                        or (request.currency and quote.currency != request.currency)):
                    raise ValueError("Identity mismatch")
                return quote, history
            quote, history = asyncio.run(prices())
            evidence = {"provider": selected.provider_name, "quote": quote.model_dump(mode="json"),
                "history_count": len(history), "first_history_date": min(row.date for row in history).isoformat(),
                "last_history_date": max(row.date for row in history).isoformat()}
    except MarketDataProviderError as error:
        code = error.code
    except Exception:
        code = "PROVIDER_PROBE_FAILED"
    run.status = "failed" if code else "success"
    run.finished_at = datetime.now(timezone.utc)
    run.fetched_count = 0 if code else 1
    run.error_count = int(bool(code))
    run.error_details_json = {"code": code} if code else None
    run.metadata_json = {**run.metadata_json, "evidence": evidence, "elapsed_seconds": round(time.monotonic() - started, 3)}
    db.commit()
    return {"processing_run_id": run.id, "provider": provider, "status": run.status,
        "failure_code": code, "checked_at": run.finished_at.isoformat(), **run.metadata_json}
