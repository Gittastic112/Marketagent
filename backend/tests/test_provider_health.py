from datetime import datetime, timezone

import pytest

from app.models.damodaran import DamodaranDatasetFile
from app.models.processing_run import ProcessingRun
from app.models.source import Source


def _provider_by_name(items: list[dict], provider_name: str) -> dict:
    return next(item for item in items if item["provider_name"] == provider_name)


def test_ai_health_does_not_claim_unimplemented_providers_are_configured(client, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("AI_DEMO_MODE", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "not-an-implemented-adapter")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "not-an-implemented-adapter")
    ai = _provider_by_name(client.get("/api/providers/health").json()["data"], "AI Provider")
    assert ai["configured"] is False
    assert ai["status"] == "missing_key"


def test_explicit_demo_mode_wins_over_a_configured_real_key(client, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("AI_DEMO_MODE", "true")
    ai = _provider_by_name(client.get("/api/providers/health").json()["data"], "AI Provider")
    assert ai["status"] == "mock"
    assert ai["freshness_label"] == "simulated"
    assert ai["last_success_at"] is None


def test_health_preserves_long_history_without_loading_every_run(db):
    from datetime import timedelta
    from sqlalchemy import event
    from app.services.provider_health import _latest_run_summaries

    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    db.add(ProcessingRun(run_type="sec_ingestion", started_at=start, status="success"))
    db.add_all([ProcessingRun(run_type="sec_ingestion", started_at=start + timedelta(days=index),
                              status="failed", error_count=1) for index in range(1, 71)])
    db.commit()
    db.expunge_all()
    loaded = []

    def record(run, _context):
        loaded.append(run.id)

    event.listen(ProcessingRun, "load", record)
    try:
        summary = _latest_run_summaries(db)["sec_ingestion"]
    finally:
        event.remove(ProcessingRun, "load", record)
    assert summary.consecutive_failures == 70
    assert summary.recent_run_count == 71
    assert summary.last_success_at.date() == start.date()
    assert summary.latest_run_status == "failed"
    assert len(loaded) == 2


def test_ai_health_reflects_failed_generation_probe(client, db, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    db.add(ProcessingRun(run_type="ai_provider_probe", source_type="gemini",
        started_at=datetime.now(timezone.utc), finished_at=datetime.now(timezone.utc),
        status="failed", error_count=1, metadata_json={"model":"gemini-2.5-flash"},
        error_details_json={"code":"AI_MODEL_UNAVAILABLE"}))
    db.commit()
    ai = _provider_by_name(client.get("/api/providers/health").json()["data"], "AI Provider")
    assert ai["configured"] is True
    assert ai["status"] == "failing"
    assert ai["latest_run_status"] == "failed"


def test_ai_probe_success_for_other_model_is_not_current_proof(client, db, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-configured-model")
    db.add(ProcessingRun(run_type="ai_provider_probe", source_type="gemini",
        started_at=datetime.now(timezone.utc), finished_at=datetime.now(timezone.utc),
        status="success", metadata_json={"model":"gemini-different-model"}))
    db.commit()
    ai = _provider_by_name(client.get("/api/providers/health").json()["data"], "AI Provider")
    assert ai["status"] == "configured" and ai["last_success_at"] is None


@pytest.mark.parametrize("identity", [
    "Market Intelligence Engine local research app contact@example.com",
    "Research app your.email@example.com",
])
def test_sec_health_does_not_accept_contact_placeholders(client, monkeypatch, identity) -> None:
    monkeypatch.setenv("SEC_USER_AGENT", identity)
    response = client.get("/api/providers/health")
    assert response.status_code == 200
    provider = _provider_by_name(response.json()["data"], "SEC EDGAR")
    assert provider["configured"] is False
    assert provider["status"] == "missing_key"
    assert "real contact email" in provider["action_required"]


def test_provider_health_reports_configuration_and_processing_run_history(client, db, monkeypatch) -> None:
    monkeypatch.setenv("SEC_USER_AGENT", "Market Intelligence Engine test@example.com")
    monkeypatch.setenv("FRED_API_KEY", "fred-key")
    monkeypatch.setenv("ALPHA_VANTAGE_API_KEY", "alpha-key")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-key")
    monkeypatch.delenv("OPENFIGI_API_KEY", raising=False)

    db.add_all(
        [
            ProcessingRun(
                run_type="sec_ingestion",
                source_type="sec",
                started_at=datetime(2026, 6, 19, 10, 0, tzinfo=timezone.utc),
                finished_at=datetime(2026, 6, 19, 10, 1, tzinfo=timezone.utc),
                status="completed",
                fetched_count=2,
                created_count=2,
            ),
            ProcessingRun(
                run_type="fred_ingestion",
                source_type="macro",
                started_at=datetime(2026, 6, 19, 11, 0, tzinfo=timezone.utc),
                finished_at=datetime(2026, 6, 19, 11, 1, tzinfo=timezone.utc),
                status="failed",
                error_count=1,
                error_details_json={"error": "rate limited"},
            ),
            DamodaranDatasetFile(
                uploaded_filename="country-risk-premiums.xlsx",
                dataset_code="country_risk_premiums",
                country="Global",
                source_file_type="xlsx",
            ),
        ]
    )
    db.commit()

    response = client.get("/api/providers/health")

    assert response.status_code == 200
    body = response.json()
    providers = body["data"]
    assert body["meta"]["source"] == "internal"

    sec = _provider_by_name(providers, "SEC EDGAR")
    assert sec["requirement_level"] == "core"
    assert sec["status"] == "working"
    assert sec["configured"] is True
    assert sec["last_success_at"] == "2026-06-19T10:01:00"
    assert sec["freshness_label"] == "stale"
    assert sec["data_age_hours"] > 72
    assert "Refresh" in sec["action_required"]

    fred = _provider_by_name(providers, "FRED")
    assert fred["status"] == "failing"
    assert fred["configured"] is True
    assert fred["last_failure_at"] == "2026-06-19T11:01:00"
    assert fred["failure_reason"] == "rate limited"

    market_data = _provider_by_name(providers, "Alpha Vantage")
    assert market_data["status"] == "configured"
    assert market_data["configured"] is True

    ai = _provider_by_name(providers, "AI Provider")
    assert ai["status"] == "configured"
    assert ai["configured"] is True
    assert ai["notes"] == "Gemini configured"

    openfigi = _provider_by_name(providers, "OpenFIGI")
    assert openfigi["status"] == "missing_key"
    assert openfigi["configured"] is False
    assert openfigi["requirement_level"] == "optional"
    assert openfigi["notes"] is None

    damodaran = _provider_by_name(providers, "Damodaran Benchmarks")
    assert damodaran["status"] == "working"
    assert damodaran["configured"] is True


def test_provider_health_marks_missing_required_keys(client, monkeypatch) -> None:
    monkeypatch.setenv("SEC_USER_AGENT", "Market Intelligence Engine local research app")
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
    monkeypatch.delenv("FMP_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    response = client.get("/api/providers/health")

    assert response.status_code == 200
    providers = response.json()["data"]

    assert _provider_by_name(providers, "SEC EDGAR")["status"] == "missing_key"
    assert _provider_by_name(providers, "SEC EDGAR")["requirement_level"] == "core"
    assert _provider_by_name(providers, "FRED")["status"] == "missing_key"
    assert _provider_by_name(providers, "FRED")["requirement_level"] == "optional"
    assert _provider_by_name(providers, "Alpha Vantage")["status"] == "missing_key"
    assert _provider_by_name(providers, "AI Provider")["status"] == "missing_key"
    assert _provider_by_name(providers, "India Manual Filings")["status"] == "manual_only"
    assert _provider_by_name(providers, "India Manual Filings")["requirement_level"] == "manual"


def test_provider_health_labels_explicit_yfinance_personal_mode(client, monkeypatch) -> None:
    monkeypatch.setenv("MARKET_DATA_PROVIDER", "yfinance_personal")

    response = client.get("/api/providers/health")

    assert response.status_code == 200
    provider = _provider_by_name(response.json()["data"], "yfinance (personal/unofficial)")
    assert provider["configured"] is True
    assert provider["status"] == "configured"
    assert "unofficial" in provider["notes"].lower()


def test_provider_health_classifies_latest_running_and_partial_attempts(client, db, monkeypatch) -> None:
    monkeypatch.setenv("SEC_USER_AGENT", "Market Intelligence Engine test@example.com")
    monkeypatch.setenv("FRED_API_KEY", "fred-key")
    db.add_all(
        [
            ProcessingRun(
                run_type="sec_ingestion",
                source_type="sec",
                started_at=datetime(2026, 6, 19, 9, 0, tzinfo=timezone.utc),
                finished_at=datetime(2026, 6, 19, 9, 1, tzinfo=timezone.utc),
                status="completed",
            ),
            ProcessingRun(
                run_type="sec_ingestion",
                source_type="sec",
                started_at=datetime(2026, 6, 19, 12, 0, tzinfo=timezone.utc),
                status="running",
            ),
            ProcessingRun(
                run_type="fred_ingestion",
                source_type="macro",
                started_at=datetime(2026, 6, 19, 11, 0, tzinfo=timezone.utc),
                finished_at=datetime(2026, 6, 19, 11, 2, tzinfo=timezone.utc),
                status="partial_success",
                fetched_count=4,
                created_count=3,
                error_count=1,
                error_details_json={"error": "one series rejected"},
            ),
        ]
    )
    db.commit()

    providers = client.get("/api/providers/health").json()["data"]
    sec = _provider_by_name(providers, "SEC EDGAR")
    assert sec["status"] == "running"
    assert sec["latest_run_status"] == "running"
    assert sec["last_attempt_at"] == "2026-06-19T12:00:00"
    assert sec["recent_run_count"] == 2

    fred = _provider_by_name(providers, "FRED")
    assert fred["status"] == "partial"
    assert fred["latest_run_status"] == "partial"
    assert fred["failure_reason"] == "one series rejected"


def test_provider_health_reports_owned_rss_source_coverage(client, db) -> None:
    db.add_all(
        [
            Source(name="Feed One", source_type="rss", base_url="https://one.example/feed", active=True),
            Source(name="Feed Two", source_type="rss", base_url="https://two.example/feed", active=True),
            Source(name="Disabled Feed", source_type="rss", base_url="https://off.example/feed", active=False),
        ]
    )
    db.commit()

    rss = _provider_by_name(client.get("/api/providers/health").json()["data"], "RSS Feeds")
    assert rss["configured_source_count"] == 2
    assert rss["coverage_state"] == "2 active RSS sources"
    assert rss["freshness_label"] == "never_run"
    assert "Run RSS Feeds ingestion" in rss["action_required"]
