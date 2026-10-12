"""Opt-in concurrency proof in a disposable PostgreSQL database, never normal data."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime
from decimal import Decimal
import os
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import Company, MarketPrice, ProcessingRun, RawDocument
from app.providers.filings import ManualFilingCreate
from app.services.filing_manual import create_manual_filing
from app.services.market_data import ingestion
from app.services.market_data.base import MarketQuoteResult, MarketHistoryResult
from app.services import valuation_source_refresh as refresh


@pytest.fixture
def pg_engine():
    url = os.getenv("INGESTION_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires a disposable PostgreSQL ingestion environment")
    parsed = make_url(url)
    assert parsed.drivername.startswith("postgresql") and parsed.database.endswith("_e2e")
    base = create_engine(url)
    schema = "ingestion_test_" + uuid4().hex
    with base.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = base.execution_options(schema_translate_map={None: schema})
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        # Only the isolated schema allocated above; never public or caller data.
        with base.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        base.dispose()


def company_id(engine):
    with Session(engine) as db:
        company = Company(ticker="MOCK", name="Mock Data concurrency", market="US",
                          primary_exchange="NASDAQ", local_symbol="MOCK", currency="USD")
        db.add(company)
        db.commit()
        return company.id


def test_concurrent_price_retries_have_one_daily_row(pg_engine, monkeypatch):
    identity = company_id(pg_engine)
    fetched = Barrier(2)
    class Provider:
        provider_name = "mock_concurrency"
        async def get_quote(self, request):
            return MarketQuoteResult(provider_name=self.provider_name, provider_symbol="MOCK", ticker="MOCK",
                market="US", exchange="NASDAQ", currency="USD", current_price=Decimal("15"),
                source_timestamp=datetime(2026, 10, 9, tzinfo=UTC))
        async def get_historical_prices(self, request, days):
            fetched.wait(timeout=10)
            return [MarketHistoryResult(provider_name=self.provider_name, provider_symbol="MOCK", ticker="MOCK",
                market="US", exchange="NASDAQ", currency="USD", close_price=Decimal("14"), date=date(2026, 10, 9))]
    monkeypatch.setattr(ingestion, "get_market_data_provider", Provider)
    monkeypatch.setattr(ingestion, "check_price_valuation_divergence", lambda *args, **kwargs: None)
    def ingest():
        with Session(pg_engine, autoflush=False) as db:
            return asyncio.run(ingestion.ingest_company_prices(db, company=db.get(Company, identity), user_id="mock"))
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: ingest(), range(2)))
    assert sum(row.created_count for row in results) == 1
    assert sum(row.skipped_duplicate_count for row in results) == 3
    with Session(pg_engine) as db:
        assert db.scalar(select(func.count(MarketPrice.id))) == 1
        assert db.scalar(select(MarketPrice)).price_type == "end_of_day"
        assert list(db.scalars(select(ProcessingRun.status))) == ["completed", "completed"]


def test_concurrent_manual_retry_retains_one_source_document(pg_engine):
    identity = company_id(pg_engine)
    start = Barrier(2)
    def create():
        with Session(pg_engine, autoflush=False) as db:
            company = db.get(Company, identity)
            start.wait(timeout=10)
            return create_manual_filing(db, company, ManualFilingCreate(
                document_type="annual_report", title="Mock Data", raw_text="Revenue 100")).id
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: create(), range(2)))
    assert results[0] == results[1]
    with Session(pg_engine) as db:
        assert db.scalar(select(func.count(RawDocument.id))) == 1


def test_worker_lock_prevents_overlap_then_recovers_interrupted_children(pg_engine, monkeypatch):
    monkeypatch.setenv("VALUATION_REFRESH_ENABLED", "false")
    from app.core.config import get_settings
    get_settings.cache_clear()
    with Session(pg_engine) as db:
        parent = ProcessingRun(run_type=refresh.RUN_TYPE, status="running", started_at=datetime.now(UTC),
                               metadata_json={"user_id": "mock"})
        db.add(parent)
        db.commit()
        child = ProcessingRun(run_type="market_data_ingestion", status="running", started_at=datetime.now(UTC),
                              metadata_json={"parent_run_id": parent.id})
        db.add(child)
        db.commit()
        with pg_engine.connect() as lock:
            assert lock.scalar(text("SELECT pg_try_advisory_lock(:key)"), {"key": refresh.LOCK_ID})
            assert refresh.run_refresh_cycle(db) == {"processed": 0, "locked": True}
            db.refresh(parent)
            assert parent.status == "running"
            lock.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": refresh.LOCK_ID})
        assert refresh.run_refresh_cycle(db) == {"processed": 0, "locked": False}
        db.refresh(parent)
        db.refresh(child)
        assert parent.status == child.status == "failed"
        assert parent.finished_at and child.finished_at
