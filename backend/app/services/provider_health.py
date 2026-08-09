import os
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas import ProviderHealthRead
from app.models.damodaran import DamodaranDatasetFile
from app.models.processing_run import ProcessingRun
from app.models.source import Source


COMPLETED_STATUSES = {"completed", "success"}
FAILED_STATUSES = {"failed", "error"}
RUNNING_STATUSES = {"running", "in_progress", "queued"}
PARTIAL_STATUSES = {"partial", "completed_with_errors"}
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
            market="US",
            configured=_valid_sec_user_agent(_env("SEC_USER_AGENT")),
            run_summary=latest_runs.get("sec_ingestion"),
            missing_action="Set SEC_USER_AGENT with a real contact email before SEC ingestion.",
            rate_limit_status="10 requests/second",
            coverage_state="US Public Companies",
        ),
        _configured_provider(
            provider_name="FRED",
            capability="macro",
            market="US",
            configured=bool(_env("FRED_API_KEY")),
            run_summary=latest_runs.get("fred_ingestion"),
            missing_action="Set FRED_API_KEY to enable FRED macro ingestion.",
            rate_limit_status="120 requests/minute",
            coverage_state="US Macro Indicators",
        ),
        _configured_provider(
            provider_name=market_provider,
            capability="market_prices",
            market="US/IN",
            configured=_market_data_key_configured(market_provider),
            run_summary=latest_runs.get("market_data_ingestion"),
            missing_action=_market_data_missing_action(market_provider),
            configured_notes=_market_data_provider_notes(market_provider),
            rate_limit_status="5 requests/minute (Free)" if market_provider == "Alpha Vantage" else "Unknown",
            coverage_state="US & Select Global Equities",
        ),
        _configured_provider(
            provider_name="AI Provider",
            capability="ai_analysis",
            market=None,
            configured=bool(_first_configured_ai_provider()),
            run_summary=None,
            missing_action="Set GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY to enable non-mock AI output.",
            configured_notes=_ai_provider_notes(),
            unconfigured_status="mock" if _ai_demo_mode_enabled() else "missing_key",
            rate_limit_status="Depends on Tier",
            coverage_state="Global",
        ),
        _configured_provider(
            provider_name="OpenFIGI",
            capability="identity_resolution",
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
    return bool(value and "@" in value and value != DEFAULT_SEC_USER_AGENT)


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
    if provider_name == "yfinance (personal/unofficial)":
        return True
    if provider_name.startswith("Unsupported"):
        return False
    key_name = _market_data_key_name(provider_name)
    return bool(key_name and _env(key_name))


def _market_data_missing_action(provider_name: str) -> str:
    if provider_name.startswith("Unsupported"):
        return "Set MARKET_DATA_PROVIDER to alphavantage, fmp, or yfinance_personal."
    key_name = _market_data_key_name(provider_name)
    return f"Set {key_name} to enable provider-backed market prices."


def _market_data_provider_notes(provider_name: str) -> str | None:
    if provider_name == "yfinance (personal/unofficial)":
        return "Explicit local personal-use opt-in; unofficial data must be verified for material decisions."
    return None


def _first_configured_ai_provider() -> str | None:
    for provider_name, env_name in (
        ("Gemini", "GEMINI_API_KEY"),
        ("OpenAI", "OPENAI_API_KEY"),
        ("Anthropic", "ANTHROPIC_API_KEY"),
    ):
        if _env(env_name):
            return provider_name
    return None


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
    market: str | None,
    configured: bool,
    run_summary: RunSummary | None,
    missing_action: str,
    configured_notes: str | None = None,
    unconfigured_status: str = "missing_key",
    rate_limit_status: str | None = None,
    coverage_state: str | None = None,
) -> ProviderHealthRead:
    summary = run_summary or RunSummary()
    status = _status_for_configured_provider(configured=configured, summary=summary, unconfigured_status=unconfigured_status)
    return ProviderHealthRead(
        provider_name=provider_name,
        capability=capability,
        market=market,
        status=status,
        configured=configured,
        last_attempt_at=summary.last_attempt_at,
        latest_run_status=summary.latest_run_status,
        recent_run_count=summary.recent_run_count,
        consecutive_failures=summary.consecutive_failures,
        last_success_at=summary.last_success_at,
        last_failure_at=summary.last_failure_at,
        failure_reason=summary.failure_reason,
        freshness_label=_freshness_for_status(status),
        notes=configured_notes,
        action_required=None if configured else missing_action,
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


def _latest_run_summaries(db: Session) -> dict[str, RunSummary]:
    runs = list(db.scalars(select(ProcessingRun).order_by(ProcessingRun.started_at.desc(), ProcessingRun.id.desc())))
    runs_by_type: dict[str, list[ProcessingRun]] = {}
    for run in runs:
        runs_by_type.setdefault(run.run_type, []).append(run)
    return {run_type: _summarize_runs(items) for run_type, items in runs_by_type.items()}


def _normalized_run_status(run: ProcessingRun) -> str:
    status = run.status.lower()
    if status in RUNNING_STATUSES:
        return "running"
    if status in FAILED_STATUSES:
        return "failed"
    if status in PARTIAL_STATUSES or (status in COMPLETED_STATUSES and run.error_count > 0):
        return "partial"
    if status in COMPLETED_STATUSES:
        return "completed"
    return "unknown"


def _summarize_runs(runs: list[ProcessingRun]) -> RunSummary:
    latest = runs[0]
    latest_status = _normalized_run_status(latest)
    last_success = next(
        ((run.finished_at or run.started_at) for run in runs if _normalized_run_status(run) == "completed"),
        None,
    )
    last_failure_run = next(
        (run for run in runs if _normalized_run_status(run) in {"failed", "partial"}),
        None,
    )
    consecutive_failures = 0
    for run in runs:
        if _normalized_run_status(run) != "failed":
            break
        consecutive_failures += 1
    return RunSummary(
        last_attempt_at=latest.started_at,
        latest_run_status=latest_status,
        recent_run_count=len(runs),
        consecutive_failures=consecutive_failures,
        last_success_at=last_success,
        last_failure_at=(last_failure_run.finished_at or last_failure_run.started_at) if last_failure_run else None,
        failure_reason=_failure_reason(last_failure_run) if last_failure_run else None,
    )


def _failure_reason(run: ProcessingRun) -> str | None:
    details = run.error_details_json or {}
    if isinstance(details, dict):
        value = details.get("error") or details.get("message") or details.get("detail")
        return str(value) if value else None
    return str(details)


def _damodaran_health(db: Session) -> ProviderHealthRead:
    latest_file = db.scalar(select(DamodaranDatasetFile).order_by(DamodaranDatasetFile.imported_at.desc()))
    configured = latest_file is not None
    return ProviderHealthRead(
        provider_name="Damodaran Benchmarks",
        capability="benchmarks",
        market="Global",
        status="working" if configured else "not_configured",
        configured=configured,
        last_success_at=latest_file.imported_at if latest_file is not None else None,
        freshness_label="fresh" if configured else "missing",
        notes=f"Latest dataset: {latest_file.dataset_code}" if latest_file is not None else None,
        action_required=None if configured else "Import Damodaran benchmark files before benchmark-derived autofill.",
        rate_limit_status="N/A (Static File)",
        coverage_state="Global Baselines",
    )


def _rss_health(db: Session, run_summary: RunSummary | None) -> ProviderHealthRead:
    has_active_source = db.scalar(select(Source.id).where(Source.source_type == "rss", Source.active.is_(True))) is not None
    return _configured_provider(
        provider_name="RSS Feeds",
        capability="news",
        market="US/IN",
        configured=has_active_source,
        run_summary=run_summary,
        missing_action="Add at least one active RSS source before RSS ingestion.",
        configured_notes="At least one active RSS source configured",
        rate_limit_status="Depends on Feed",
        coverage_state="News/Blogs",
    )
