from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import MarketPrice, PortfolioBenchmarkConfig, PortfolioSnapshot, PortfolioTransaction
from app.models.market_price import DAILY_PRICE_TYPES
from app.services.fx_rates import FxRateUnavailable, convert_amount
from app.services.portfolio_cash_flows import normalize_external_cash_flows
from app.services.portfolio_replay import snapshot_replay_is_verified


@dataclass(frozen=True)
class BenchmarkPricePoint:
    price_base: Decimal
    market_price_id: int
    price_date: date
    fx_observation_id: int | None
    fx_date: date
    target_date: date
    price_age_days: int
    fx_age_days: int
    is_stale: bool

    def evidence(self):
        return {key: getattr(self, key) for key in ("market_price_id", "price_date", "fx_observation_id",
            "fx_date", "target_date", "price_age_days", "fx_age_days", "is_stale")}


def _series(db, config, start_date, end_date):
    if not config.provider_name or (config.provider_name != "manual" and not config.provider_symbol):
        return None
    conditions = (MarketPrice.ticker == config.ticker, MarketPrice.company_id == config.benchmark_company_id,
        MarketPrice.currency == config.currency, MarketPrice.provider_name == config.provider_name,
        MarketPrice.provider_symbol == config.provider_symbol, MarketPrice.price_type.in_(DAILY_PRICE_TYPES))
    identities = db.execute(select(MarketPrice.market, MarketPrice.exchange, MarketPrice.adjustment_state,
                                   MarketPrice.price_type, MarketPrice.claim_type)
        .where(*conditions, MarketPrice.as_of_date.between(start_date - timedelta(days=5), end_date))
        .distinct().limit(2)).all()
    if len(identities) != 1:
        return None
    market, venue, adjustment, kind, claim = identities[0]
    if adjustment not in {"adjusted", "split_adjusted", "unadjusted", "not_applicable"}:
        return None
    if kind == "end_of_day" and (not market or not venue or adjustment == "not_applicable"):
        return None
    if kind == "Mock Data" and "mock" not in config.provider_name.lower():
        return None
    return (*conditions, MarketPrice.market == market, MarketPrice.exchange == venue,
            MarketPrice.adjustment_state == adjustment, MarketPrice.price_type == kind, MarketPrice.claim_type == claim)


def _price_point(
    db: Session,
    series,
    target_date: date,
    base_currency: str,
) -> BenchmarkPricePoint | None:
    if series is None:
        return None
    query = select(MarketPrice).where(*series, MarketPrice.as_of_date <= target_date)
    price = db.scalar(query.order_by(MarketPrice.as_of_date.desc(), MarketPrice.id.desc()).limit(1))
    if price is None or not Decimal(str(price.price)).is_finite() or price.price <= 0:
        return None
    conflict = db.scalar(select(MarketPrice.id).where(
        *series, MarketPrice.as_of_date == price.as_of_date, MarketPrice.price != price.price).limit(1))
    if conflict is not None:
        return None
    try:
        price_base, fx = convert_amount(
            db,
            price.price,
            price.currency,
            base_currency,
            target_date,
            stale_after_days=5,
        )
    except FxRateUnavailable:
        return None
    return BenchmarkPricePoint(
        price_base=price_base,
        market_price_id=price.id,
        price_date=price.as_of_date,
        fx_observation_id=fx.observation_id,
        fx_date=fx.as_of_date,
        target_date=target_date,
        price_age_days=(target_date - price.as_of_date).days,
        fx_age_days=fx.age_days,
        is_stale=(target_date - price.as_of_date).days > 5 or fx.is_stale,
    )


def calculate_benchmark_opportunity_cost(
    db: Session,
    portfolio_id: int,
    start_date: date,
    end_date: date,
) -> dict:
    config = db.scalar(
        select(PortfolioBenchmarkConfig).where(
            PortfolioBenchmarkConfig.portfolio_id == portfolio_id,
            PortfolioBenchmarkConfig.active.is_(True),
            PortfolioBenchmarkConfig.effective_from <= start_date,
        )
    )
    snapshots = list(
        db.scalars(
            select(PortfolioSnapshot).where(
                PortfolioSnapshot.portfolio_id == portfolio_id,
                PortfolioSnapshot.snapshot_date.in_((start_date, end_date)),
            )
        )
    )
    by_date = {snapshot.snapshot_date: snapshot for snapshot in snapshots}
    start = by_date.get(start_date)
    end = by_date.get(end_date)
    warnings = ["Benchmark comparison is price-return based unless the stored series is explicitly adjusted.",
        "Every benchmark quote and required FX observation must be within five calendar days of its boundary or flow date; no trading-calendar adjustment is assumed."]
    if config is None:
        return {
            "calculation_status": "not_configured",
            "portfolio_id": portfolio_id,
            "start_date": start_date,
            "end_date": end_date,
            "benchmark_ticker": None,
            "benchmark_return": None,
            "portfolio_return": None,
            "return_spread": None,
            "benchmark_ending_value": None,
            "actual_ending_value": float(end.total_portfolio_value) if end and end.total_portfolio_value is not None else None,
            "opportunity_cost": None,
            "opportunity_cost_percent": None,
            "warnings": ["Select a benchmark before calculating opportunity cost."],
            "source_snapshot_ids": [snapshot.id for snapshot in snapshots],
            "source_market_price_ids": [],
            "source_transaction_ids": [],
        }
    if (
        start is None
        or end is None
        or start.calculation_status != "complete"
        or end.calculation_status != "complete"
        or start.total_portfolio_value is None
        or end.total_portfolio_value is None
        or start.base_currency != end.base_currency
        or not start.base_currency or len(start.base_currency) != 3 or not start.base_currency.isalpha()
    ):
        warnings.append("Complete snapshots are required on both comparison boundaries.")
        return {
            "calculation_status": "not_available",
            "portfolio_id": portfolio_id,
            "start_date": start_date,
            "end_date": end_date,
            "benchmark_ticker": config.ticker,
            "benchmark_return": None,
            "portfolio_return": None,
            "return_spread": None,
            "benchmark_ending_value": None,
            "actual_ending_value": None,
            "opportunity_cost": None,
            "opportunity_cost_percent": None,
            "warnings": warnings,
            "source_snapshot_ids": [snapshot.id for snapshot in snapshots],
            "source_market_price_ids": [],
            "source_transaction_ids": [],
        }

    series = _series(db, config, start_date, end_date)
    if series is None:
        warnings.append("The configured benchmark needs a single identifiable listing, provider symbol and adjustment basis.")
    start_price = _price_point(db, series, start_date, start.base_currency)
    end_price = _price_point(db, series, end_date, start.base_currency)
    if start_price is not None:
        action = db.scalar(select(PortfolioTransaction.id).where(PortfolioTransaction.portfolio_id == portfolio_id,
            PortfolioTransaction.company_id == config.benchmark_company_id, PortfolioTransaction.ticker == config.ticker,
            PortfolioTransaction.transaction_type.in_(("split", "bonus")),
            PortfolioTransaction.transaction_date > start_price.price_date,
            PortfolioTransaction.transaction_date <= end_date).limit(1))
        if action is not None and db.get(MarketPrice, start_price.market_price_id).adjustment_state != "adjusted":
            warnings.append("This benchmark spans a recorded share action without a supported adjusted price series.")
            end_price = None
    flow_report = normalize_external_cash_flows(
        db,
        portfolio_id,
        start_date=start_date,
        end_date=end_date,
        target_currency=start.base_currency,
        max_fx_age_days=5,
    )
    evidence = [point.evidence() for point in (start_price, end_price) if point]
    flow_evidence = [{"transaction_id": flow.transaction_id, "target_date": flow.transaction_date,
        "fx_date": flow.fx_as_of_date, "fx_observation_id": flow.fx_observation_id,
        "fx_age_days": (flow.transaction_date - flow.fx_as_of_date).days, "is_stale": flow.fx_is_stale} for flow in flow_report.flows]
    if start_price is None or end_price is None or start_price.is_stale or end_price.is_stale or not flow_report.complete:
        warnings.append("Current-enough benchmark prices, historical FX, and all external flows are required for this period.")
        return {
            "calculation_status": "not_available",
            "portfolio_id": portfolio_id,
            "start_date": start_date,
            "end_date": end_date,
            "benchmark_ticker": config.ticker,
            "benchmark_return": None,
            "portfolio_return": None,
            "return_spread": None,
            "benchmark_ending_value": None,
            "actual_ending_value": float(end.total_portfolio_value),
            "opportunity_cost": None,
            "opportunity_cost_percent": None,
            "warnings": warnings,
            "source_snapshot_ids": [start.id, end.id],
            "source_market_price_ids": [point.market_price_id for point in (start_price, end_price) if point],
            "source_transaction_ids": flow_report.missing_transaction_ids,
            "price_evidence": evidence, "flow_fx_evidence": flow_evidence, "base_currency": start.base_currency,
        }

    units = Decimal(start.total_portfolio_value) / start_price.price_base
    source_price_ids = [start_price.market_price_id, end_price.market_price_id]
    for flow in flow_report.flows:
        flow_price = _price_point(db, series, flow.transaction_date, start.base_currency)
        if flow_price is not None:
            evidence.append(flow_price.evidence())
        if flow_price is None or flow_price.is_stale:
            warnings.append(f"Benchmark price is unavailable for external flow transaction {flow.transaction_id}.")
            return {
                "calculation_status": "not_available",
                "portfolio_id": portfolio_id,
                "start_date": start_date,
                "end_date": end_date,
                "benchmark_ticker": config.ticker,
                "benchmark_return": None,
                "portfolio_return": None,
                "return_spread": None,
                "benchmark_ending_value": None,
                "actual_ending_value": float(end.total_portfolio_value),
                "opportunity_cost": None,
                "opportunity_cost_percent": None,
                "warnings": warnings,
                "source_snapshot_ids": [start.id, end.id],
                "source_market_price_ids": source_price_ids,
                "source_transaction_ids": [item.transaction_id for item in flow_report.flows],
                "price_evidence": evidence, "flow_fx_evidence": flow_evidence, "base_currency": start.base_currency,
            }
        units += flow.amount_base / flow_price.price_base
        source_price_ids.append(flow_price.market_price_id)

    benchmark_ending_value = units * end_price.price_base
    actual_ending_value = Decimal(end.total_portfolio_value)
    opportunity_cost = benchmark_ending_value - actual_ending_value
    benchmark_return = float(end_price.price_base / start_price.price_base - Decimal("1"))
    net_external = flow_report.net_external_cash_flow or Decimal("0")
    invested_base = Decimal(start.total_portfolio_value) + net_external
    portfolio_return = (
        float((actual_ending_value - net_external) / Decimal(start.total_portfolio_value) - Decimal("1"))
        if Decimal(start.total_portfolio_value) > 0
        else None
    )
    if flow_report.flows:
        # Boundary price return and a cash-subtracted portfolio return are not
        # comparable under flows, even if deposits and withdrawals net to zero.
        benchmark_return = portfolio_return = None
        warnings.append("Return percentages and spread are unavailable with external cash flows until both sides use the same return method; the matched-flow ending-wealth comparison remains available.")
    replay_verified = snapshot_replay_is_verified(start, db) and snapshot_replay_is_verified(end, db)
    if not replay_verified:
        warnings.append("Legacy snapshot history or subsequently changed activity is unverified for transaction replay; benchmark comparison is provisional.")
    return {
        "calculation_status": "complete" if replay_verified else "partial",
        "portfolio_id": portfolio_id,
        "start_date": start_date,
        "end_date": end_date,
        "benchmark_ticker": config.ticker,
        "benchmark_return": benchmark_return,
        "portfolio_return": portfolio_return,
        "return_spread": portfolio_return - benchmark_return if portfolio_return is not None else None,
        "benchmark_ending_value": float(benchmark_ending_value),
        "actual_ending_value": float(actual_ending_value),
        "opportunity_cost": float(opportunity_cost),
        "opportunity_cost_percent": float(opportunity_cost / invested_base) if invested_base > 0 else None,
        "warnings": warnings,
        "source_snapshot_ids": [start.id, end.id],
        "source_market_price_ids": sorted(set(source_price_ids)),
        "source_transaction_ids": [flow.transaction_id for flow in flow_report.flows],
        "price_evidence": evidence, "flow_fx_evidence": flow_evidence, "base_currency": start.base_currency,
    }
