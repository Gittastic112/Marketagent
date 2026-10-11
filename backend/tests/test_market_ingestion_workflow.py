import asyncio
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.models import Company, MarketPrice
from app.models.processing_run import ProcessingRun
from app.services.market_data.base import MarketDataProviderError, MarketHistoryResult, MarketQuoteResult


class Provider:
    provider_name = "fixture"

    async def get_quote(self, request):
        return MarketQuoteResult(provider_name=self.provider_name, provider_symbol=request.ticker,
            ticker=request.ticker, market="US", exchange="NASDAQ", currency="USD",
            current_price=Decimal("15"), source_timestamp=datetime(2026, 8, 1, tzinfo=timezone.utc))

    async def get_historical_prices(self, request, days=365):
        return [MarketHistoryResult(provider_name=self.provider_name, provider_symbol=request.ticker,
            ticker=request.ticker, market="US", exchange="NASDAQ", currency="USD",
            close_price=Decimal("14"), date=date(2026, 8, 1))]


def setup(db, monkeypatch):
    from app.services.market_data import ingestion
    company = Company(ticker="TST", name="Mock Data", market="US", primary_exchange="NASDAQ", currency="USD")
    db.add(company); db.commit()
    monkeypatch.setattr(ingestion, "get_market_data_provider", lambda: Provider())
    return company, ingestion


def test_ingestion_same_date_quote_history_has_one_price_and_retry_is_idempotent(db, monkeypatch):
    company, ingestion = setup(db, monkeypatch)
    first = asyncio.run(ingestion.ingest_company_prices(db, company=company, user_id="admin_user_id_fallback"))
    second = asyncio.run(ingestion.ingest_company_prices(db, company=company, user_id="admin_user_id_fallback"))
    assert first.created_count == 1 and first.skipped_duplicate_count == 1
    assert second.created_count == 0 and second.skipped_duplicate_count == 2
    assert db.query(MarketPrice).count() == 1
    assert db.scalar(select(MarketPrice)).price_type == "end_of_day"


def test_ingestion_rolls_back_prices_if_downstream_work_fails(db, monkeypatch):
    company, ingestion = setup(db, monkeypatch)
    def fail(*args, **kwargs):
        raise RuntimeError("private provider response")
    monkeypatch.setattr(ingestion, "check_price_valuation_divergence", fail)
    with pytest.raises(MarketDataProviderError) as error:
        asyncio.run(ingestion.ingest_company_prices(db, company=company, user_id="admin_user_id_fallback"))
    assert "private" not in str(error.value)
    assert db.query(MarketPrice).count() == 0
    run = db.scalar(select(ProcessingRun))
    assert run.status == "failed" and run.created_count == 0 and run.error_count == 1
    assert error.value.processing_run_id == run.id


def test_missing_configuration_is_audited_before_fetch(db, monkeypatch):
    company, ingestion = setup(db, monkeypatch)
    def missing():
        raise MarketDataProviderError(code="PROVIDER_NOT_CONFIGURED", message="Not configured", provider="fixture")
    monkeypatch.setattr(ingestion, "get_market_data_provider", missing)
    with pytest.raises(MarketDataProviderError):
        asyncio.run(ingestion.ingest_company_prices(db, company=company, user_id="admin_user_id_fallback"))
    assert db.scalar(select(ProcessingRun)).status == "failed"


def test_quote_only_compatibility_uses_same_service_without_history(db, monkeypatch):
    company, ingestion = setup(db, monkeypatch)
    async def forbidden(*args, **kwargs):
        pytest.fail("Quote-only request must not fetch history")
    monkeypatch.setattr(Provider, "get_historical_prices", forbidden)
    result = asyncio.run(ingestion.ingest_company_prices(db, company=company,
        user_id="admin_user_id_fallback", include_history=False))
    assert result.fetched_count == 1
    assert db.scalar(select(ProcessingRun)).run_type == "market_quote_ingestion"
