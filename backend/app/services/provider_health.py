import os
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import case, func, select, or_
from sqlalchemy.orm import Session

from app.schemas.operations import ProviderHealthRead
from app.models.damodaran import DamodaranDatasetFile
from app.models.processing_run import ProcessingRun
from app.models.source import Source
from app.providers.ai_provider import DEFAULT_GEMINI_MODEL
from app.services.sec_ingestion import get_valid_sec_user_agent


COMPLETED_STATUSES = {"completed", "success"}
FAILED_STATUSES = {"failed", "error"}
RUNNING_STATUSES = {"running", "in_progress", "queued"}
PARTIAL_STATUSES = {"partial", "partial_success", "completed_with_errors"}
DEFAULT_SEC_USER_AGENT = "Market Intelligence Engine local research app"


@dataclass(frozen=True)
class RunSummary:
    last_attempt_at: datetime | None = None
    latest_run_status: str | None = None
    recent_run_count: int = 0
    consecutive_failures: int = 0
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    failure_reason: str | None = None


def get_provider_health(db: Session) -> list[ProviderHealthRead]:
    latest_runs = _latest_run_summaries(db)
    market_provider = _market_data_provider_name()

    return [
        _configured_provider(
            provider_name="SEC EDGAR",
            capability="filings",
            requirement_level="core",
            market="US",
            configured=_valid_sec_user_agent(_env("SEC_USER_AGENT")),
            run_summary=latest_runs.get("sec_ingestion"),
            missing_action="Set SEC_USER_AGENT with a real contact email before SEC ingestion.",
            rate_limit_status="10 requests/second",
            coverage_state="US Public Companies",
            freshness_threshold_hours=72,
        ),
        _configured_provider(
            provider_name="FRED",
            capability="macro",
            requirement_level="optional",
            market="US",
            configured=bool(_env("FRED_API_KEY")),
            run_summary=latest_runs.get("fred_ingestion"),
            missing_action="Set FRED_API_KEY to enable FRED macro ingestion.",
            rate_limit_status="120 requests/minute",
            coverage_state="US Macro Indicators",
            freshness_threshold_hours=168,
        ),
        _configured_provider(
            provider_name=market_provider,
            capability="market_prices",
            requirement_level="optional",
            market="US/IN",
            configured=_market_data_key_configured(market_provider),
            run_summary=latest_runs.get("market_data_ingestion"),
            missing_action=_market_data_missing_action(market_provider),
            configured_notes=_market_data_provider_notes(market_provider),
            unconfigured_status="not_configured" if market_provider != "Alpha Vantage" else "missing_key",
            rate_limit_status="5 requests/minute (Free)" if market_provider == "Alpha Vantage" else "Unknown",
            coverage_state="US & Select Global Equities",
            freshness_threshold_hours=24,
        ),
        _configured_provider(
            provider_name="AI Provider",
            capability="ai_analysis",
            requirement_level="optional",
            market=None,
            configured=bool(_first_configured_ai_provider()) and not _ai_demo_mode_enabled(),
            run_summary=None if _ai_demo_mode_enabled() else _ai_probe_summary(db),
            missing_action="Disable AI_DEMO_MODE to use configured Gemini." if _ai_demo_mode_enabled() else "Set GEMINI_API_KEY and an accessible GEMINI_MODEL to enable non-mock AI output.",
            configured_notes=_ai_provider_notes(),
            unconfigured_status="mock" if _ai_demo_mode_enabled() else "missing_key",
            rate_limit_status="Depends on Tier",
            coverage_state="Global",
        ),
        _configured_provider(
            provider_name="OpenFIGI",
            capability="identity_resolution",
            requirement_level="optional",
            market=None,
            configured=bool(_env("OPENFIGI_API_KEY")),
            run_summary=None,
            missing_action="Set OPENFIGI_API_KEY to improve cross-market identity resolution.",
            configured_notes="Optional identity provider configured",
            rate_limit_status="25 requests/minute",
            coverage_state="Global Equities",
        ),
        _damodaran_health(db),
        _rss_health(db, latest_runs.get("rss_ingestion")),
        ProviderHealthRead(
            provider_name="India Manual Filings",
            capability="filings",
            requirement_level="manual",
            market="IN",
            status="manual_only",
            configured=True,
            freshness_label="manual",
            notes="India automated filing provider is not configured; use manual upload or filing links.",
            action_required="Upload annual reports, quarterly results, or exchange announcements manually.",
            rate_limit_status="N/A (Manual)",
            coverage_state="Indian Public Companies",
        ),
    ]


def _env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _valid_sec_user_agent(value: str | None) -> bool:
    if not value or "@" not in value or value == DEFAULT_SEC_USER_AGENT:
        return False
    try:
        get_valid_sec_user_agent(value)
    except ValueError:
        return False
    return True


def _market_data_provider_name() -> str:
    provider = (_env("MARKET_DATA_PROVIDER") or "alphavantage").lower()
    if provider == "fmp":
        return "Financial Modeling Prep"
    if provider == "yfinance_personal":
        return "yfinance (personal/unofficial)"
    if provider not in {"alphavantage", "alpha_vantage"}:
        return f"Unsupported ({provider})"
    return "Alpha Vantage"


def _market_data_key_name(provider_name: str) -> str | None:
    if provider_name == "Financial Modeling Prep":
        return "FMP_API_KEY"
    if provider_name == "Alpha Vantage":
        return "ALPHA_VANTAGE_API_KEY"
    return None


def _market_data_key_configured(provider_name: str) -> bool:
    if provider_name == "Financial Modeling Prep":
        return False  # Adapter is a stub, even when a key exists.
    if provider_name == "yfinance (personal/unofficial)":
        return True
    if provider_name.startswith("Unsupported"):
        return False
    key_name = _market_data_key_name(provider_name)
    return bool(key_name and _env(key_name))


def _market_data_missing_action(provider_name: str) -> str:
    if provider_name == "Financial Modeling Prep":
        return "Not available yet: FMP ingestion is not implemented. Select an implemented provider."
    if provider_name.startswith("Unsupported"):
        return "Set MARKET_DATA_PROVIDER to alphavantage or yfinance_personal."
    key_name = _market_data_key_name(provider_name)
    return f"Set {key_name} to enable provider-backed market prices."


def _market_data_provider_notes(provider_name: str) -> str | None:
    if provider_name == "yfinance (personal/unofficial)":
        return "Explicit local personal-use opt-in; unofficial data must be verified for material decisions."
    return None


def _first_configured_ai_provider() -> str | None:
    # Keep health aligned with select_ai_provider: other adapters are not built.
    return "Gemini" if _env("GEMINI_API_KEY") else None


def _ai_probe_summary(db: Session) -> RunSummary | None:
    # A successful check of a different model is not proof for this configuration.
    model = _env("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL
    return _run_summaries(db,
        ProcessingRun.run_type == "ai_provider_probe",
        ProcessingRun.source_type == "gemini",
        ProcessingRun.metadata_json["model"].as_string() == model,
    ).get("ai_provider_probe")


def _ai_provider_notes() -> str | None:
    provider = _first_configured_ai_provider()
    if provider:
        return f"{provider} configured"
    if _ai_demo_mode_enabled():
        return "Mock AI demo mode enabled; outputs are simulated and visibly labeled."
    return None


def _ai_demo_mode_enabled() -> bool:
    return (_env("AI_DEMO_MODE") or "false").lower() in {"1", "true", "yes", "on"}


def _configured_provider(
    *,
    provider_name: str,
    capability: str,
    requirement_level: str,
    market: str | None,
    configured: bool,
    run_summary: RunSummary | None,
    missing_action: str,
    configured_notes: str | None = None,
    unconfigured_status: str = "missing_key",
    rate_limit_status: str | None = None,
    coverage_state: str | None = None,
    freshness_threshold_hours: int | None = None,
    configured_source_count: int | None = None,
) -> ProviderHealthRead:
    summary = run_summary or RunSummary()
    status = _status_for_configured_provider(configured=configured, summary=summary, unconfigured_status=unconfigured_status)
    data_age_hours = _data_age_hours(summary.last_success_at)
    freshness_label = _freshness_for_provider(
        status=status,
        configured=configured,
        has_run=summary.last_attempt_at is not None,
        data_age_hours=data_age_hours,
        threshold_hours=freshness_threshold_hours,
    )
    return ProviderHealthRead(
        provider_name=provider_name,
        capability=capability,
        requirement_level=requirement_level,
        market=market,
        status=status,
        configured=configured,
        last_attempt_at=summary.last_attempt_at,
        latest_run_status=summary.latest_run_status,
        recent_run_count=summary.recent_run_count,
        consecutive_failures=summary.consecutive_failures,
        data_age_hours=data_age_hours,
        freshness_threshold_hours=freshness_threshold_hours,
        configured_source_count=configured_source_count,
        last_success_at=summary.last_success_at,
        last_failure_at=summary.last_failure_at,
        failure_reason=summary.failure_reason,
        freshness_label=freshness_label,
        notes=configured_notes if configured else None,
        action_required=_action_for_provider(
            configured=configured,
            status=status,
            freshness_label=freshness_label,
            missing_action=missing_action,
            provider_name=provider_name,
        ),
        rate_limit_status=rate_limit_status,
        coverage_state=coverage_state,
    )


def _status_for_configured_provider(*, configured: bool, summary: RunSummary, unconfigured_status: str = "missing_key") -> str:
    if not configured:
        return unconfigured_status
    if summary.latest_run_status == "running":
        return "running"
    if summary.latest_run_status == "partial":
        return "partial"
    if summary.latest_run_status == "failed":
        return "failing"
    if summary.last_success_at:
        return "working"
    return "configured"


def _freshness_for_status(status: str) -> str:
    if status == "working":
        return "fresh"
    if status == "running":
        return "updating"
    if status == "partial":
        return "partial"
    if status == "failing":
        return "error"
    if status == "manual_only":
        return "manual"
    if status in {"missing_key", "not_configured"}:
        return "missing"
    if status == "mock":
        return "simulated"
    return "unknown"


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def _data_age_hours(last_success_at: datetime | None) -> float | None:
    if last_success_at is None:
        return None
    age = datetime.now(timezone.utc) - _as_utc(last_success_at)
    return round(max(age.total_seconds(), 0) / 3600, 1)


def _freshness_for_provider(
    *,
    status: str,
    configured: bool,
    has_run: bool,
    data_age_hours: float | None,
    threshold_hours: int | None,
) -> str:
    base = _freshness_for_status(status)
    if not configured or status in {"running", "partial", "failing", "manual_only", "mock"}:
        return base
    if not has_run:
        return "never_run"
    if data_age_hours is not None and threshold_hours is not None and data_age_hours > threshold_hours:
        return "stale"
    return base


def _action_for_provider(
    *, configured: bool, status: str, freshness_label: str, missing_action: str, provider_name: str
) -> str | None:
    if not configured:
        return missing_action
    if status == "failing":
        return f"Inspect the latest {provider_name} error and retry ingestion."
    if status == "partial":
        return f"Review rejected records from the latest {provider_name} run."
    if freshness_label == "never_run":
        return f"Run {provider_name} ingestion to establish freshness."
    if freshness_label == "stale":
        return f"Refresh {provider_name}; the latest successful data is outside its freshness threshold."
    return None


def _latest_run_summaries(db: Session) -> dict[str, RunSummary]:
    provider = (_env("MARKET_DATA_PROVIDER") or "alphavantage").lower()
    provider = "alpha_vantage" if provider == "alphavantage" else provider
    return _run_summaries(db, ProcessingRun.run_type.in_(
        ("sec_ingestion", "fred_ingestion", "market_data_ingestion", "rss_ingestion")
    ), or_(ProcessingRun.run_type != "market_data_ingestion", ProcessingRun.source_type == provider))


def _run_summaries(db: Session, *conditions) -> dict[str, RunSummary]:
    """Load at most one row per status/type, retaining all-history counts/dates."""
    status = func.lower(ProcessingRun.status)
    normalized = case(
        (status.in_(RUNNING_STATUSES), "running"),
        (status.in_(FAILED_STATUSES), "failed"),
        (status.in_(PARTIAL_STATUSES) | (status.in_(COMPLETED_STATUSES) & (ProcessingRun.error_count > 0)), "partial"),
        (status.in_(COMPLETED_STATUSES), "completed"),
        else_="unknown",
    )
    ordering = (ProcessingRun.started_at.desc(), ProcessingRun.id.desc())
    ranked = select(
        ProcessingRun.id,
        normalized.label("normalized_status"),
        func.row_number().over(partition_by=ProcessingRun.run_type, order_by=ordering).label("position"),
        func.row_number().over(partition_by=(ProcessingRun.run_type, normalized), order_by=ordering).label("status_position"),
        func.count().over(partition_by=ProcessingRun.run_type).label("total"),
    ).where(*conditions).subquery()
    selected = db.execute(select(ProcessingRun, ranked.c.position, ranked.c.total, ranked.c.normalized_status)
                          .join(ranked, ranked.c.id == ProcessingRun.id)
                          .where(ranked.c.status_position == 1)
                          .order_by(ranked.c.position)).all()
    grouped: dict[str, list] = {}
    for row in selected:
        grouped.setdefault(row[0].run_type, []).append(row)
    summaries = {}
    for run_type, rows in grouped.items():
        latest, _, total, latest_status = rows[0]
        success = next((row[0] for row in rows if row[3] == "completed"), None)
        failure = next((row[0] for row in rows if row[3] in {"failed", "partial"}), None)
        first_nonfailure = next((row[1] for row in rows if row[3] != "failed"), total + 1)
        summaries[run_type] = RunSummary(
            last_attempt_at=latest.started_at, latest_run_status=latest_status,
            recent_run_count=total, consecutive_failures=first_nonfailure - 1,
            last_success_at=(success.finished_at or success.started_at) if success else None,
            last_failure_at=(failure.finished_at or failure.started_at) if failure else None,
            failure_reason=_failure_reason(failure) if failure else None,
        )
    return summaries


def _failure_reason(run: ProcessingRun) -> str | None:
    details = run.error_details_json or {}
    if isinstance(details, dict):
        value = details.get("error") or details.get("message") or details.get("detail") or details.get("code") or details.get("error_type")
        if not value and isinstance(details.get("errors"), list) and details["errors"]:
            value = details["errors"][0]
        return str(value) if value else None
    return str(details)


def _damodaran_health(db: Session) -> ProviderHealthRead:
    latest_file = db.scalar(select(DamodaranDatasetFile).order_by(DamodaranDatasetFile.imported_at.desc()).limit(1))
    configured = latest_file is not None
    age_hours = _data_age_hours(latest_file.imported_at) if latest_file is not None else None
    threshold_hours = 24 * 400
    stale = age_hours is not None and age_hours > threshold_hours
    return ProviderHealthRead(
        provider_name="Damodaran Benchmarks",
        capability="benchmarks",
        requirement_level="core",
        market="Global",
        status="working" if configured else "not_configured",
        configured=configured,
        last_success_at=latest_file.imported_at if latest_file is not None else None,
        data_age_hours=age_hours,
        freshness_threshold_hours=threshold_hours,
        configured_source_count=1 if configured else 0,
        freshness_label="stale" if stale else ("fresh" if configured else "missing"),
        notes=f"Latest dataset: {latest_file.dataset_code}" if latest_file is not None else None,
        action_required=(
            "Import a newer Damodaran benchmark dataset."
            if stale
            else (None if configured else "Import Damodaran benchmark files before benchmark-derived autofill.")
        ),
        rate_limit_status="N/A (Static File)",
        coverage_state="Global Baselines",
    )


def _rss_health(db: Session, run_summary: RunSummary | None) -> ProviderHealthRead:
    active_source_count = int(
        db.scalar(select(func.count(Source.id)).where(Source.source_type == "rss", Source.active.is_(True))) or 0
    )
    has_active_source = active_source_count > 0
    return _configured_provider(
        provider_name="RSS Feeds",
        capability="news",
        requirement_level="optional",
        market="US/IN",
        configured=has_active_source,
        run_summary=run_summary,
        missing_action="Add at least one active RSS source before RSS ingestion.",
        configured_notes="At least one active RSS source configured",
        rate_limit_status="Depends on Feed",
        coverage_state=f"{active_source_count} active RSS sources",
        freshness_threshold_hours=24,
        configured_source_count=active_source_count,
    )
