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


def test_ingestion_same_date_quote_and_history_remain_distinct_and_retry_is_idempotent(db, monkeypatch):
    company, ingestion = setup(db, monkeypatch)
    first = asyncio.run(ingestion.ingest_company_prices(db, company=company, user_id="admin_user_id_fallback"))
    second = asyncio.run(ingestion.ingest_company_prices(db, company=company, user_id="admin_user_id_fallback"))
    assert first.created_count == 2 and first.skipped_duplicate_count == 0
    assert second.created_count == 0 and second.skipped_duplicate_count == 2
    assert db.query(MarketPrice).count() == 2
    close = db.scalar(select(MarketPrice).where(MarketPrice.price_type == "end_of_day"))
    assert close.id != first.market_price.id
    prior_close = (close.id, close.price, close.adjustment_state)
    asyncio.run(ingestion.ingest_company_prices(db, company=company, user_id="admin_user_id_fallback", include_history=False))
    db.refresh(close)
    assert (close.id, close.price, close.adjustment_state) == prior_close


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


def test_cancelled_fetch_is_a_finished_failure_without_partial_prices(db, monkeypatch):
    company, ingestion = setup(db, monkeypatch)
    async def cancelled(*args, **kwargs):
        raise asyncio.CancelledError()
    monkeypatch.setattr(Provider, "get_quote", cancelled)
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(ingestion.ingest_company_prices(db, company=company, user_id="owner", parent_run_id=12))
    run = db.scalar(select(ProcessingRun))
    assert run.status == "failed" and run.finished_at
    assert run.error_details_json["code"] == "MARKET_DATA_CANCELLED"
    assert run.metadata_json["parent_run_id"] == 12
    assert run.source_type == "fixture"
    assert db.query(MarketPrice).count() == 0


def test_provider_cannot_store_another_security_under_the_selected_company(db, monkeypatch):
    company, ingestion = setup(db, monkeypatch)
    original = Provider.get_quote
    async def wrong_security(self, request):
        result = await original(self, request)
        return result.model_copy(update={"ticker": "OTHER"})
    monkeypatch.setattr(Provider, "get_quote", wrong_security)
    with pytest.raises(MarketDataProviderError) as error:
        asyncio.run(ingestion.ingest_company_prices(db, company=company, user_id="owner"))
    assert error.value.code == "PROVIDER_IDENTITY_MISMATCH"
    assert db.query(MarketPrice).count() == 0
    assert db.scalar(select(ProcessingRun)).status == "failed"

@pytest.mark.parametrize("history_first", [True, False])
def test_both_ingestion_orders_preserve_chart_basis_and_distinct_quote(db, monkeypatch, history_first):
    from app.services.market_data.persistence import persist_history_point, persist_quote, request_for_company
    from app.services.price_timeline import company_timeline
    company, _ = setup(db, monkeypatch)
    request = request_for_company(company)
    source = Provider()
    quote = asyncio.run(source.get_quote(request)).model_copy(update={"provider_name": "verified_test", "current_price": Decimal("104")})
    close = asyncio.run(source.get_historical_prices(request, 5))[0].model_copy(update={
        "provider_name": "verified_test", "close_price": Decimal("100"), "adjustment_state": "unadjusted"})
    def history():
        persist_history_point(db, company=company, point=close)
        db.flush()
    def current():
        persist_quote(db, company=company, quote=quote)
        db.flush()
    writes = (history, current) if history_first else (current, history)
    for write in (*writes, *writes):
        write()
    report = company_timeline(db, company.id, "synthetic-owner", None, None)
    assert db.query(MarketPrice).count() == 2
    assert len(report.points) == 1 and report.points[0].price == 100 and report.series.adjustment == "unadjusted"
    assert company.market_data.current_price == 104
