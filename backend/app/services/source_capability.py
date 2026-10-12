from datetime import datetime

from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.market_source import MarketSourceCapability
from app.services.sec_ingestion import get_valid_sec_user_agent


SUPPORTED_MARKETS = {"US", "IN"}


DEFAULT_SOURCE_CAPABILITIES = [
    {
        "market": "US", "source_type": "macro", "provider_name": "FRED",
        "capability": "fred_macro", "status": "not_configured", "requires_api_key": True,
        "freshness_expected_seconds": 86_400,
        "notes": "Configured FRED ingestion; stored series coverage and freshness require separate checks.",
    },
    {
        "market": "US",
        "source_type": "filings",
        "provider_name": "SEC EDGAR",
        "capability": "sec_filings",
        "status": "available",
        "requires_api_key": False,
        "freshness_expected_seconds": 86_400,
        "notes": "SEC EDGAR submissions and filing documents. Requires a valid SEC_USER_AGENT.",
    },
    {
        "market": "US",
        "source_type": "fundamentals",
        "provider_name": "SEC EDGAR",
        "capability": "sec_fundamentals",
        "status": "available",
        "requires_api_key": False,
        "freshness_expected_seconds": 86_400,
        "notes": "SEC companyfacts XBRL data. Requires a valid SEC_USER_AGENT.",
    },
    {
        "market": "US",
        "source_type": "market_prices",
        "provider_name": "Alpha Vantage/FMP",
        "capability": "market_prices",
        "status": "not_configured",
        "requires_api_key": True,
        "freshness_expected_seconds": 3_600,
        "notes": "Provider-backed US prices require ALPHA_VANTAGE_API_KEY or FMP_API_KEY.",
    },
    {
        "market": "IN",
        "source_type": "filings",
        "provider_name": "NSE/BSE",
        "capability": "corporate_announcements",
        "status": "manual_only",
        "requires_api_key": False,
        "freshness_expected_seconds": None,
        "notes": "Official exchange pages exist, but automated provider ingestion is not enabled.",
    },
    {
        "market": "IN",
        "source_type": "fundamentals",
        "provider_name": "Manual Upload",
        "capability": "financial_statements",
        "status": "manual_only",
        "requires_api_key": False,
        "freshness_expected_seconds": None,
        "notes": "Use manual entries or uploads until a licensed India fundamentals provider is configured.",
    },
    {
        "market": "IN",
        "source_type": "market_prices",
        "provider_name": "Alpha Vantage/FMP",
        "capability": "market_prices",
        "status": "not_configured",
        "requires_api_key": True,
        "freshness_expected_seconds": 3_600,
        "notes": "Provider-backed India prices require symbol support and ALPHA_VANTAGE_API_KEY or FMP_API_KEY.",
    },
    {
        "market": "IN",
        "source_type": "valuation_benchmarks",
        "provider_name": "Damodaran",
        "capability": "damodaran_benchmarks",
        "status": "available",
        "requires_api_key": False,
        "freshness_expected_seconds": None,
        "notes": "Imported Damodaran industry valuation benchmark files are available locally.",
    },
    {
        "market": "IN",
        "source_type": "macro",
        "provider_name": "Damodaran",
        "capability": "macro_sensitivity",
        "status": "available",
        "requires_api_key": False,
        "freshness_expected_seconds": None,
        "notes": "Imported macro duration and macro sensitivity files are available locally.",
    },
]


class SourceCapabilityDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    market: str
    source_type: str
    provider_name: str
    capability: str
    status: str
    requires_api_key: bool
    freshness_expected_seconds: int | None
    notes: str | None
    updated_at: datetime


def normalize_market(market: str | None) -> str | None:
    if market is None:
        return None
    normalized = market.strip().upper()
    if not normalized:
        return None
    if normalized not in SUPPORTED_MARKETS:
        raise ValueError(f"Unsupported market {normalized}")
    return normalized


def ensure_default_source_capabilities(db: Session) -> None:
    existing = set(db.execute(select(MarketSourceCapability.market, MarketSourceCapability.capability)).all())
    changed = False
    for item in DEFAULT_SOURCE_CAPABILITIES:
        if (item["market"], item["capability"]) in existing:
            continue
        try:
            with db.begin_nested():
                db.add(MarketSourceCapability(**item))
                db.flush()
            changed = True
        except IntegrityError:
            # Concurrent US/India page reads may initialize the same defaults.
            pass
    if changed:
        db.commit()


def list_source_capabilities(
    db: Session,
    settings: Settings,
    market: str | None = None,
) -> list[SourceCapabilityDTO]:
    normalized_market = normalize_market(market)
    ensure_default_source_capabilities(db)

    query = select(MarketSourceCapability).order_by(
        MarketSourceCapability.market,
        MarketSourceCapability.source_type,
        MarketSourceCapability.capability,
    )
    if normalized_market is not None:
        query = query.where(MarketSourceCapability.market == normalized_market)

    return [_with_effective_status(row, settings) for row in db.scalars(query)]


def _with_effective_status(row: MarketSourceCapability, settings: Settings) -> SourceCapabilityDTO:
    status = row.status
    notes = row.notes
    provider_name = row.provider_name
    requires_api_key = row.requires_api_key

    if row.capability == "market_prices":
        selected = settings.market_data_provider.strip().lower()
        requires_api_key = selected in {"alphavantage", "alpha_vantage", "fmp"}
        if selected in {"alphavantage", "alpha_vantage"}:
            provider_name = "Alpha Vantage"
            status = "available" if settings.alpha_vantage_api_key else "not_configured"
            notes = "Selected price adapter. Requires its own API key; symbol coverage, stored dates and failures are separate."
        elif selected == "yfinance_personal":
            provider_name, status = "yfinance personal-use", "available"
            notes = "Explicitly selected personal-use adapter. No API key; timing and delay may be unknown. Check stored coverage and Data Health."
        elif selected == "fmp":
            provider_name, status = "FMP", "not_supported"
            notes = "Not available yet: the FMP adapter is not implemented, even with a key. No provider coverage is implied."
        else:
            provider_name, status = "Unsupported provider", "not_supported"
            notes = "The selected price adapter is unsupported. No provider coverage or automatic fallback is available."
    elif row.capability in {"sec_filings", "sec_fundamentals"}:
        try:
            configured = bool(settings.sec_user_agent and get_valid_sec_user_agent(settings.sec_user_agent))
        except ValueError:
            configured = False
        status = "available" if configured else "not_configured"
        notes = "SEC ingestion requires a configured contact. Availability does not certify successful fetches, reviewed financials or current coverage."
    elif row.capability == "fred_macro":
        status = "available" if settings.fred_api_key else "not_configured"
        notes = "FRED ingestion is implemented and requires its API key. Check stored series coverage, observation dates and Data Health; these are US proxies."

    return SourceCapabilityDTO(
        id=row.id,
        market=row.market,
        source_type=row.source_type,
        provider_name=provider_name,
        capability=row.capability,
        status=status,
        requires_api_key=requires_api_key,
        freshness_expected_seconds=row.freshness_expected_seconds,
        notes=notes,
        updated_at=row.updated_at,
    )
