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


def test_competing_financial_candidate_reviews_reject_the_outdated_writer(pg_engine):
    from fastapi import HTTPException
    from app.models import FinancialExtractionCandidate, Source
    from app.services.financial_extraction import override_candidate_value
    identity = company_id(pg_engine)
    with Session(pg_engine) as db:
        source = Source(name="Mock Data concurrent financial review", source_type="manual", active=True)
        db.add(source); db.flush()
        document = RawDocument(company_id=identity, source_id=source.id, document_type="annual_report", title="Mock Data candidate concurrency",
                               raw_text="Revenue 100", content_hash="mock-candidate-concurrency")
        db.add(document); db.flush()
        candidate = FinancialExtractionCandidate(company_id=identity, raw_document_id=document.id, metric_code="revenue",
            reported_label="Revenue", value=100, unit="USD million", fiscal_year=2025, source_text="Revenue 100")
        db.add(candidate); db.commit()
        candidate_id, inspected_at = candidate.id, candidate.updated_at
    start = Barrier(2)
    def write(value):
        with Session(pg_engine) as db:
            start.wait(timeout=10)
            try:
                override_candidate_value(db, candidate_id, value, "USD million", inspected_at)
                return 200, value
            except HTTPException as error:
                return error.status_code, value
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(write, [200, 300]))
    assert sorted(status for status, _ in results) == [200, 409]
    with Session(pg_engine) as db:
        assert db.get(FinancialExtractionCandidate, candidate_id).value == next(value for status, value in results if status == 200)


def test_due_brief_cycle_on_postgres_records_one_audited_snapshot(pg_engine):
    from datetime import time, timedelta
    from app.models import DailyBrief, DailyBriefSchedule, User
    from app.services.daily_brief_schedule import configure_daily_brief_schedule, run_due_daily_brief_schedules
    now = datetime.now(UTC)
    with Session(pg_engine) as db:
        db.add(User(id="mock-due-cycle", email="mock-due@example.invalid", name="Mock Data scheduler"))
        db.commit()
        schedule = configure_daily_brief_schedule(db, user_id="mock-due-cycle", enabled=True,
            timezone_name="UTC", local_time=time(7), days_of_week=list(range(7)), now=now - timedelta(days=1))
        schedule.next_run_at = now - timedelta(minutes=1)
        db.commit()
        first = run_due_daily_brief_schedules(db, user_id="mock-due-cycle", now=now)
        second = run_due_daily_brief_schedules(db, user_id="mock-due-cycle", now=now)
        assert first["briefs_created"] == 1 and second["briefs_created"] == 0
        assert db.scalar(select(func.count()).select_from(DailyBrief)) == 1
        stored = db.scalar(select(DailyBriefSchedule))
        assert stored.last_status == "success" and stored.next_run_at > now
        run = db.scalar(select(ProcessingRun).where(ProcessingRun.run_type == "daily_brief_schedule"))
        assert run.status == "success" and run.finished_at is not None
        assert run.metadata_json["generation_mode"] == "deterministic_no_external_ai"


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


@pytest.mark.parametrize("existing", [False, True])
def test_concurrent_sec_retries_keep_one_identity_and_one_text(pg_engine, monkeypatch, existing):
    from app.models import Source
    from app.services import sec_ingestion as sec
    identity = company_id(pg_engine)
    filing = sec.SecFilingMetadata("0000000001-26-000001", "10-K", date(2026, 1, 1),
        filing_url="https://www.sec.gov/Archives/edgar/data/1/mock.htm")
    with Session(pg_engine, autoflush=False) as db:
        source = Source(name="Mock Data SEC concurrency", source_type="sec")
        db.add(source); db.commit()
        source_id = source.id
        if existing:
            sec.ingest_sec_filing_metadata(db, source_id, identity, [filing])
    fetched = Barrier(2)
    def fetch(*args, **kwargs):
        fetched.wait(timeout=10)
        return "Mock Data immutable SEC text"
    monkeypatch.setattr(sec, "fetch_sec_filing_text", fetch)
    def ingest(_):
        with Session(pg_engine, autoflush=False) as db:
            return sec.ingest_sec_filing_metadata(db, source_id, identity, [filing, filing], download_text=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(ingest, range(2)))
    assert sum(r.created_count for r in results) == int(not existing)
    assert sum(r.completed_text_count for r in results) == int(existing)
    assert sum(r.error_count for r in results) == 0
    assert sum(r.skipped_duplicate_count for r in results) == 3
    with Session(pg_engine) as db:
        document = db.scalar(select(RawDocument))
        assert db.scalar(select(func.count()).select_from(RawDocument)) == 1
        assert document.raw_text == "Mock Data immutable SEC text"


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


def test_competing_saved_valuation_versions_keep_one_winner_and_immutable_history(pg_engine):
    from app.models import User
    from app.models.dcf import DcfAssumptionSet, DcfOutput, ValuationModel
    from app.schemas.valuation_inputs import DcfAssumptionVersionWrite
    from app.services.assumption_versions import AssumptionVersionConflict, create_assumption_version
    from test_implied_pricing_integrity import valid_inputs

    identity = company_id(pg_engine)
    with Session(pg_engine) as db:
        db.add(User(id="mock-valuation-owner", email="mock-valuation@example.invalid", name="Mock Data"))
        db.flush()
        model = ValuationModel(company_id=identity, user_id="mock-valuation-owner", name="Mock Data concurrent save")
        db.add(model)
        db.flush()
        old = create_assumption_version(db, model, DcfAssumptionVersionWrite(**valid_inputs()))
        db.commit()
        model_id, old_id, old_updated = model.id, old.id, old.updated_at
        original_output = db.scalar(select(DcfOutput).where(DcfOutput.assumption_set_id == old_id))
        original_equity = original_output.equity_value

    start = Barrier(2)
    def save(story):
        with Session(pg_engine, autoflush=False) as db:
            model = db.get(ValuationModel, model_id)
            start.wait(timeout=10)
            try:
                row = create_assumption_version(db, model, DcfAssumptionVersionWrite(
                    base_assumption_set_id=old_id, base_assumption_set_updated_at=old_updated, story_text=story))
                db.commit()
                return ("created", row.id)
            except AssumptionVersionConflict:
                db.rollback()
                return ("conflict", None)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(save, ["Mock Data writer A", "Mock Data writer B"]))
    assert sorted(status for status, _ in results) == ["conflict", "created"]
    with Session(pg_engine) as db:
        rows = list(db.scalars(select(DcfAssumptionSet).order_by(DcfAssumptionSet.id)))
        assert len(rows) == 2
        assert rows[0].id == old_id and rows[0].story_text is None
        assert rows[0].updated_at == old_updated
        assert rows[1].story_text in {"Mock Data writer A", "Mock Data writer B"}
        assert rows[1].cash == rows[0].cash == 0
        outputs = list(db.scalars(select(DcfOutput).order_by(DcfOutput.id)))
        assert len(outputs) == 2 and outputs[0].equity_value == original_equity


def test_identical_reviewed_save_retries_share_one_receipt_and_version(pg_engine):
    from app.models import User
    from app.models.dcf import DcfAssumptionSet, DcfDecisionLog, ValuationModel
    from app.schemas.valuation_inputs import DcfAssumptionVersionWrite
    from app.services.assumption_versions import create_assumption_version, preview_assumption_version
    from test_implied_pricing_integrity import valid_inputs

    identity = company_id(pg_engine)
    with Session(pg_engine) as db:
        db.add(User(id="mock-retry-owner", email="mock-retry@example.invalid")); db.flush()
        model = ValuationModel(company_id=identity, user_id="mock-retry-owner", name="Mock Data reviewed retry")
        db.add(model); db.flush()
        old = create_assumption_version(db, model, DcfAssumptionVersionWrite(**valid_inputs()))
        db.commit()
        payload = dict(base_assumption_set_id=old.id, base_assumption_set_updated_at=old.updated_at,
            cash=10, minority_interests=0, preferred_stock=0, employee_options_value=0, valuation_date="2026-11-12")
        preview = preview_assumption_version(db, model, DcfAssumptionVersionWrite(**payload))
        assert preview["ready"]
        command = DcfAssumptionVersionWrite(**payload, preview_hash=preview["preview_hash"],
            submission_id=uuid4(), change_reason="Mock Data concurrent duplicate")
        model_id = model.id
    start = Barrier(2)
    def save(_):
        with Session(pg_engine, autoflush=False) as db:
            model = db.get(ValuationModel, model_id); start.wait(timeout=10)
            row = create_assumption_version(db, model, command); db.commit()
            return row.id
    with ThreadPoolExecutor(max_workers=2) as pool:
        ids = list(pool.map(save, range(2)))
    assert ids[0] == ids[1]
    with Session(pg_engine) as db:
        assert db.query(DcfAssumptionSet).count() == 2
        assert db.query(DcfDecisionLog).count() == 1


def test_competing_stale_acknowledgements_record_one_review(pg_engine):
    from app.models import User
    from app.models.dcf import DcfAssumptionSet, ValuationModel, DcfDecisionLog
    from app.schemas.valuation import StaleValuationReviewCreate
    from app.services.valuation_review import acknowledge_stale_review, stale_review_token
    identity = company_id(pg_engine)
    with Session(pg_engine) as db:
        db.add(User(id="mock-reviewer", email="mock-reviewer@example.invalid", name="Mock Data reviewer"))
        db.flush()
        model = ValuationModel(company_id=identity, name="Mock Data review race", user_id="mock-reviewer")
        db.add(model); db.flush()
        row = DcfAssumptionSet(valuation_model_id=model.id, is_stale=True, stale_reason="Mock Data new filing")
        db.add(row); db.commit()
        row_id = row.id
        request = StaleValuationReviewCreate(expected_updated_at=row.updated_at, review_token=stale_review_token(row),
            reason="Mock Data reviewed; retain the assumptions.")
    started = Barrier(2)
    def review(_):
        with Session(pg_engine) as db:
            started.wait(timeout=10)
            try:
                acknowledge_stale_review(db, row_id, request, "mock-reviewer")
                db.commit()
                return 200
            except ValueError:
                db.rollback()
                return 409
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(review, range(2))) == [200, 409]
    with Session(pg_engine) as db:
        assert db.scalar(select(func.count()).select_from(DcfDecisionLog)) == 1
def test_competing_daily_brief_workers_share_one_durable_claim(pg_engine, monkeypatch):
    from datetime import time, timedelta
    from threading import Event as ThreadEvent
    from app.models import User, DailyBriefSchedule, DailyBrief
    from app.services import daily_brief_schedule as schedules
    owner = "mock-concurrent-brief"
    now = datetime.now(UTC)
    with Session(pg_engine) as db:
        db.add(User(id=owner, email="brief@example.invalid", name="Mock Data worker")); db.commit()
        schedule = schedules.configure_daily_brief_schedule(db, user_id=owner, enabled=True, timezone_name="UTC",
            local_time=time(7), days_of_week=list(range(7)), now=now - timedelta(days=1))
        schedule.next_run_at = now - timedelta(minutes=1); db.commit()
        identity = schedule.id
    entered, release = ThreadEvent(), ThreadEvent()
    original = schedules.MorningBriefingEngine.get_or_generate_briefing
    def held(db, user_id, target_date):
        with Session(pg_engine) as observer:
            row = observer.get(DailyBriefSchedule, identity)
            assert row.last_processing_run_id is not None
            assert observer.get(ProcessingRun, row.last_processing_run_id).status == "running"
        entered.set()
        assert release.wait(15)
        return original(db, user_id, target_date)
    monkeypatch.setattr(schedules.MorningBriefingEngine, "get_or_generate_briefing", held)
    def run():
        with Session(pg_engine) as db:
            return schedules.run_due_daily_brief_schedules(db, now=now)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(run)
        try:
            assert entered.wait(15)
            assert pool.submit(run).result(15)["schedules_checked"] == 0
        finally:
            release.set()
        assert first.result(15)["briefs_created"] == 1
    with Session(pg_engine) as db:
        assert db.scalar(select(func.count()).select_from(DailyBrief)) == 1
        assert db.scalar(select(func.count()).select_from(ProcessingRun)) == 1
        assert db.scalar(select(ProcessingRun.status)) == "success"


def test_replacement_brief_worker_does_not_claim_a_late_workers_snapshot(pg_engine, monkeypatch):
    from datetime import time, timedelta
    from threading import Event as ThreadEvent
    from sqlalchemy import event
    from app.models import User, DailyBrief
    from app.services import daily_brief_schedule as schedules

    now = datetime.now(UTC)
    owner = "mock-expired-brief"
    with Session(pg_engine) as db:
        db.add(User(id=owner, email="expired@example.invalid", name="Mock Data expired worker")); db.commit()
        schedule = schedules.configure_daily_brief_schedule(db, user_id=owner, enabled=True,
            timezone_name="UTC", local_time=time(7), days_of_week=list(range(7)), now=now - timedelta(days=1))
        schedule.next_run_at = now - timedelta(minutes=1); db.commit()
    entered, release, replacement_claim = ThreadEvent(), ThreadEvent(), ThreadEvent()
    original = schedules.MorningBriefingEngine.generate_briefing
    def held(*args, **kwargs):
        entered.set()
        assert release.wait(15)
        return original(*args, **kwargs)
    monkeypatch.setattr(schedules.MorningBriefingEngine, "generate_briefing", held)
    def observe_claim(connection, cursor, statement, parameters, context, executemany):
        if entered.is_set() and statement.startswith("UPDATE ") and "SET last_processing_run_id=" in statement:
            replacement_claim.set()
    event.listen(pg_engine, "before_cursor_execute", observe_claim)
    def run(at):
        with Session(pg_engine) as db:
            return schedules.run_due_daily_brief_schedules(db, now=at)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(run, now)
        try:
            assert entered.wait(15)
            replacement = pool.submit(run, now + timedelta(minutes=11))
            # The replacement reaches its claim while the original still holds
            # the owner lock. Its claim can wait; a second committed run is not
            # a prerequisite for releasing the original worker.
            assert replacement_claim.wait(15)
        finally:
            release.set()
            event.remove(pg_engine, "before_cursor_execute", observe_claim)
        assert first.result(15)["schedules_completed"] == 0
        assert replacement.result(15)["briefs_created"] == 0
    with Session(pg_engine) as db:
        assert db.scalar(select(func.count()).select_from(DailyBrief)) == 1
        assert sorted(db.scalars(select(ProcessingRun.status))) == ["failed", "success"]
