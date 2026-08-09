from datetime import datetime, timezone

from app.models.damodaran import DamodaranDatasetFile
from app.models.processing_run import ProcessingRun


def _provider_by_name(items: list[dict], provider_name: str) -> dict:
    return next(item for item in items if item["provider_name"] == provider_name)


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
    assert sec["status"] == "working"
    assert sec["configured"] is True
    assert sec["last_success_at"] == "2026-06-19T10:01:00"
    assert sec["freshness_label"] == "fresh"

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
    assert _provider_by_name(providers, "FRED")["status"] == "missing_key"
    assert _provider_by_name(providers, "Alpha Vantage")["status"] == "missing_key"
    assert _provider_by_name(providers, "AI Provider")["status"] == "missing_key"
    assert _provider_by_name(providers, "India Manual Filings")["status"] == "manual_only"


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
                status="completed",
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
