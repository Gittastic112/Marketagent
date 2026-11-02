from datetime import UTC, datetime
from types import SimpleNamespace
import pytest

from sqlalchemy import select

from app.core.config import get_settings
from app.models import Company, ProcessingRun
from app.models.user import User
from app.services import valuation_source_refresh as refresh


def configured_company(db):
    company = Company(name="Mock Data company", ticker="Q", market="US", currency="USD",
        cik="1234", primary_exchange="NASDAQ", local_symbol="Q")
    db.add(company)
    db.commit()
    return company


def test_cancel_queued_refresh_preserves_history_and_allows_explicit_requeue(client, db, monkeypatch):
    company = configured_company(db)
    monkeypatch.setattr(refresh, "execute_refresh", lambda *a: pytest.fail("Cancellation must not fetch sources"))
    queued = client.post(f"/companies/{company.id}/valuation-source-refresh").json()["data"]
    response = client.post(f"/valuation-source-refresh/{queued['id']}/cancel")
    assert response.status_code == 200
    canceled = response.json()["data"]
    assert canceled["status"] == "cancelled"
    assert canceled["started_at"] == queued["started_at"]
    assert canceled["finished_at"] is not None
    assert canceled["steps"] == []
    row = db.get(ProcessingRun, queued["id"])
    db.refresh(row)
    assert row.metadata_json["cancelled_by"] == row.metadata_json["user_id"]
    assert client.post(f"/valuation-source-refresh/{row.id}/cancel").json()["data"] == canceled
    assert client.post(f"/companies/{company.id}/valuation-source-refresh").json()["data"]["id"] != queued["id"]
    assert db.get(ProcessingRun, queued["id"]) is not None


@pytest.mark.parametrize("state", ["running", "success", "failed", "wrong_owner", "wrong_type"])
def test_cancel_refuses_active_finished_and_unowned_requests(client, db, state):
    company = configured_company(db)
    queued = client.post(f"/companies/{company.id}/valuation-source-refresh").json()["data"]
    row = db.get(ProcessingRun, queued["id"])
    if state == "wrong_owner":
        row.metadata_json = {**row.metadata_json, "user_id": "other-owner"}
    elif state == "wrong_type":
        row.run_type = "unrelated_operation"
    else:
        row.status = state
    db.commit()
    response = client.post(f"/valuation-source-refresh/{row.id}/cancel")
    assert response.status_code == (404 if state.startswith("wrong_") else 409)
    db.refresh(row)
    assert row.finished_at is None
    assert row.status == ("queued" if state.startswith("wrong_") else state)


def test_queue_is_owned_deduplicated_and_does_not_fetch_in_request(client, db, monkeypatch):
    company = configured_company(db)
    monkeypatch.setattr(refresh, "extract_xbrl_candidates", lambda *a, **k: (_ for _ in ()).throw(AssertionError("No request-time fetch")))
    first = client.post(f"/companies/{company.id}/valuation-source-refresh")
    assert first.status_code == 202
    row = first.json()["data"]
    assert row["status"] == "queued"
    assert client.post(f"/companies/{company.id}/valuation-source-refresh").json()["data"]["id"] == row["id"]
    assert client.get(f"/valuation-source-refresh/{row['id']}").status_code == 200
    run = db.get(ProcessingRun, row["id"])
    run.metadata_json = {**run.metadata_json, "user_id": "someone-else"}
    db.commit()
    assert client.get(f"/valuation-source-refresh/{row['id']}").status_code == 404
    status = client.get(f"/companies/{company.id}/valuation-source-refresh").json()["data"]
    assert status["latest_run"] is None


def test_partial_provider_failure_still_prepares_owned_draft_and_sanitizes_errors(db, monkeypatch):
    company = configured_company(db)
    monkeypatch.setenv("FRED_API_KEY", "dummy-key")
    get_settings.cache_clear()
    monkeypatch.setattr(refresh, "ingest_fred_series", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("secret provider URL")))
    monkeypatch.setattr(refresh, "extract_xbrl_candidates", lambda *a, **k: {
        "fetched_count": 4, "created_count": 2, "skipped_existing_count": 2, "warnings": []})
    async def prices(*a, **k):
        return SimpleNamespace(processing_run_id=999, created_count=1)
    monkeypatch.setattr(refresh, "ingest_company_prices", prices)
    run = refresh.enqueue_company_refresh(db, company.id, "owner")
    result = refresh.execute_refresh(db, run)
    assert result.status == "partial_success"
    assert len(result.metadata_json["draft_ids"]) == 1
    assert "secret provider URL" not in str(result.metadata_json)
    assert "secret provider URL" not in str([row.error_details_json for row in db.scalars(select(ProcessingRun))])
    assert result.metadata_json["steps"][-1]["status"] == "success"


def test_weekday_schedule_is_once_per_local_day_handles_dst_and_does_not_backfill(db, monkeypatch):
    db.add(User(id="schedule-owner", email="fixture@example.invalid", name="Mock Data"))
    db.commit()
    monkeypatch.setenv("VALUATION_REFRESH_ENABLED", "true")
    monkeypatch.setenv("VALUATION_REFRESH_OWNER_ID", "schedule-owner")
    get_settings.cache_clear()
    processed = []
    def finish(db, run):
        processed.append(run.metadata_json["scheduled_for"])
        run.status = "success"
        db.commit()
    monkeypatch.setattr(refresh, "execute_refresh", finish)
    # September is EDT: 7 a.m. is 11 UTC.
    assert refresh.run_refresh_cycle(db, now=datetime(2026, 9, 22, 10, 59, tzinfo=UTC))["processed"] == 0
    assert refresh.run_refresh_cycle(db, now=datetime(2026, 9, 22, 11, 0, tzinfo=UTC))["processed"] == 1
    assert refresh.run_refresh_cycle(db, now=datetime(2026, 9, 22, 18, 0, tzinfo=UTC))["processed"] == 0
    assert refresh.run_refresh_cycle(db, now=datetime(2026, 9, 26, 15, 0, tzinfo=UTC))["processed"] == 0
    # November is EST: 7 a.m. is 12 UTC; missed days are not synthesized.
    assert refresh.run_refresh_cycle(db, now=datetime(2026, 11, 2, 11, 59, tzinfo=UTC))["processed"] == 0
    assert refresh.run_refresh_cycle(db, now=datetime(2026, 11, 2, 12, 0, tzinfo=UTC))["processed"] == 1
    assert processed == ["2026-09-22", "2026-11-02"]
    assert refresh.refresh_status(db, "another-user")["enabled"] is False


def test_interrupted_job_is_visible_and_requires_explicit_retry(db, monkeypatch):
    monkeypatch.setenv("VALUATION_REFRESH_ENABLED", "false")
    get_settings.cache_clear()
    company = configured_company(db)
    run = refresh.enqueue_company_refresh(db, company.id, "owner")
    run.status = "running"
    db.commit()
    refresh.run_refresh_cycle(db)
    db.refresh(run)
    assert run.status == "failed"
    assert run.error_details_json["error_type"] == "worker_interrupted"
    assert refresh.enqueue_company_refresh(db, company.id, "owner").id != run.id


def test_restart_finishes_only_interrupted_parents_running_children(db, monkeypatch):
    monkeypatch.setenv("VALUATION_REFRESH_ENABLED", "false")
    get_settings.cache_clear()
    company = configured_company(db)
    parent = refresh.enqueue_company_refresh(db, company.id, "owner")
    parent.status = "running"
    children = [ProcessingRun(run_type="market_data_ingestion", status=status, started_at=datetime.now(UTC),
        metadata_json={"parent_run_id": parent_id}) for parent_id, status in
        [(parent.id, "running"), (parent.id, "success"), (parent.id + 99, "running")]]
    db.add_all(children)
    db.commit()
    refresh.run_refresh_cycle(db)
    for child in children:
        db.refresh(child)
    assert children[0].status == "failed" and children[0].finished_at
    assert children[0].error_details_json["error_type"] == "worker_interrupted"
    assert children[1].status == "success"
    assert children[2].status == "running"
