from datetime import date

from sqlalchemy import select

from app.core.config import get_settings
from app.models import ProcessingRun
from app.models.macro import MacroObservation, MacroSeries
from app.providers.fred_provider import FredProvider
from app.services.macro_ingestion import ingest_fred_series, normalize_fred_series_id


SERIES_INFO = {
    "id": "NFCI",
    "title": "National Financial Conditions Index",
    "units_short": "Index",
    "frequency_short": "Weekly",
}
OBSERVATIONS = [
    {"date": "2026-08-21", "value": "-0.42"},
    {"date": "2026-08-14", "value": "-0.35"},
    {"date": "2026-08-07", "value": "."},
    {"date": "invalid", "value": "1.2"},
]


def _stub_fred(monkeypatch) -> None:
    monkeypatch.setattr(FredProvider, "fetch_series_info", lambda self, series_id: SERIES_INFO)
    monkeypatch.setattr(FredProvider, "fetch_observations", lambda self, series_id: OBSERVATIONS)


def test_fred_ingestion_normalizes_id_and_preserves_provenance(db, monkeypatch) -> None:
    _stub_fred(monkeypatch)

    result = ingest_fred_series(db, " nfci ", api_key="test-key")

    series = db.scalar(select(MacroSeries).where(MacroSeries.name == "NFCI"))
    assert result.series_id == "NFCI"
    assert result.macro_series_id == series.id
    assert result.fetched_count == 4
    assert result.created_count == 2
    assert result.skipped_missing_count == 1
    assert result.error_count == 1
    assert result.errors == ("FRED_OBSERVATION_INVALID",)
    assert series.provider_name == "FRED"
    assert series.source_url == "https://fred.stlouisfed.org/series/NFCI"
    assert len(list(db.scalars(select(MacroObservation)))) == 2


def test_fred_ingestion_is_idempotent_and_refreshes_metadata(db, monkeypatch) -> None:
    _stub_fred(monkeypatch)
    first = ingest_fred_series(db, "NFCI", api_key="test-key")
    SERIES_INFO["title"] = "Updated title"
    try:
        second = ingest_fred_series(db, "NFCI", api_key="test-key")
    finally:
        SERIES_INFO["title"] = "National Financial Conditions Index"

    series = db.scalar(select(MacroSeries).where(MacroSeries.name == "NFCI"))
    assert first.created_count == 2
    assert second.created_count == 0
    assert second.skipped_duplicate_count == 2
    assert series.description == "Updated title"
    assert len(list(db.scalars(select(MacroSeries)))) == 1


def test_fred_series_id_validation_rejects_url_or_shell_text() -> None:
    assert normalize_fred_series_id(" nfci ") == "NFCI"
    for value in ("", "https://fred.example/NFCI", "NFCI;DROP", "NFCI value"):
        try:
            normalize_fred_series_id(value)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Expected {value!r} to be rejected")


def test_fred_malformed_future_and_revision_rows_remain_visible_without_rewriting_evidence(db, monkeypatch):
    _stub_fred(monkeypatch)
    ingest_fred_series(db, "NFCI", api_key="test-key")
    monkeypatch.setattr(FredProvider, "fetch_observations", lambda *a: [
        None, {"date": "2026-08-21", "value": []}, {"date": "2999-01-01", "value": "1"},
        {"date": "2026-08-21", "value": "-0.99"},
    ])
    result = ingest_fred_series(db, "NFCI", api_key="test-key")
    assert result.error_count == 4
    assert "FRED_OBSERVATION_REVISION_REQUIRES_REVIEW" in result.errors
    assert db.scalar(select(MacroObservation).where(MacroObservation.date_recorded == date(2026, 8, 21))).value == -0.42


def test_fred_api_records_successful_processing_run(client, db, monkeypatch) -> None:
    monkeypatch.setenv("FRED_API_KEY", "test-key")
    get_settings.cache_clear()
    _stub_fred(monkeypatch)

    response = client.post("/ingest/fred-series", json={"series_id": "nfci"})

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["meta"]["source"] == "FRED"
    assert body["data"]["series_id"] == "NFCI"
    assert body["data"]["observations_created"] == 2
    assert body["data"]["observations_rejected"] == 1
    run = db.get(ProcessingRun, body["data"]["processing_run_id"])
    assert run.run_type == "fred_ingestion"
    assert run.source_type == "macro"
    assert run.status == "partial_success"
    assert run.fetched_count == 4
    assert run.created_count == 2
    assert run.error_details_json == {"errors": ["FRED_OBSERVATION_INVALID"]}
    assert run.metadata_json["macro_series_id"] == body["data"]["macro_series_id"]

    monkeypatch.setenv("FRED_API_KEY", "test-key")
    provider = next(
        item
        for item in client.get("/api/providers/health").json()["data"]
        if item["provider_name"] == "FRED"
    )
    assert provider["status"] == "partial"
    assert provider["latest_run_status"] == "partial"
    assert provider["failure_reason"] == "FRED_OBSERVATION_INVALID"


def test_fred_api_records_sanitized_provider_failure(client, db, monkeypatch) -> None:
    monkeypatch.setenv("FRED_API_KEY", "test-key")
    get_settings.cache_clear()
    monkeypatch.setattr(
        FredProvider,
        "fetch_series_info",
        lambda self, series_id: (_ for _ in ()).throw(RuntimeError("secret upstream body")),
    )

    response = client.post("/ingest/fred-series", json={"series_id": "NFCI"})

    assert response.status_code == 502
    error = response.json()["errors"][0]
    assert error["code"] == "FRED_INGESTION_FAILED"
    assert error["processing_run_id"] is not None
    assert "secret upstream body" not in response.text
    run = db.get(ProcessingRun, error["processing_run_id"])
    assert run.status == "failed"
    assert run.error_details_json == {
        "error_type": "provider_failure",
        "message": "FRED did not complete the requested ingestion.",
    }


def test_fred_api_reports_missing_configuration_without_starting_run(
    client, db, monkeypatch
) -> None:
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    get_settings.cache_clear()

    response = client.post("/ingest/fred-series", json={"series_id": "NFCI"})

    assert response.status_code == 503
    assert response.json()["errors"][0]["code"] == "FRED_API_KEY_MISSING"
    assert list(db.scalars(select(ProcessingRun))) == []
