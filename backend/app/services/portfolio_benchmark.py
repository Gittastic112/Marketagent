from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import MarketPrice, PortfolioBenchmarkConfig, PortfolioSnapshot
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


def _price_point(
    db: Session,
    config: PortfolioBenchmarkConfig,
    target_date: date,
    base_currency: str,
) -> BenchmarkPricePoint | None:
    query = select(MarketPrice).where(
        MarketPrice.ticker == config.ticker,
        MarketPrice.as_of_date <= target_date,
    )
    if config.benchmark_company_id is not None:
        query = query.where(MarketPrice.company_id == config.benchmark_company_id)
    price = db.scalar(query.order_by(MarketPrice.as_of_date.desc(), MarketPrice.id.desc()).limit(1))
    if price is None or price.price <= 0:
        return None
    try:
        price_base, fx = convert_amount(
            db,
            price.price,
            price.currency or config.currency,
            base_currency,
            target_date,
        )
    except FxRateUnavailable:
        return None
    return BenchmarkPricePoint(
        price_base=price_base,
        market_price_id=price.id,
        price_date=price.as_of_date,
        fx_observation_id=fx.observation_id,
        fx_date=fx.as_of_date,
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
    warnings = ["Benchmark comparison is price-return based unless the stored series is explicitly adjusted."]
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

    start_price = _price_point(db, config, start_date, start.base_currency)
    end_price = _price_point(db, config, end_date, start.base_currency)
    flow_report = normalize_external_cash_flows(
        db,
        portfolio_id,
        start_date=start_date,
        end_date=end_date,
    )
    if start_price is None or end_price is None or not flow_report.complete:
        warnings.append("Benchmark prices, historical FX, and all external flows are required for this period.")
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
        }

    units = Decimal(start.total_portfolio_value) / start_price.price_base
    source_price_ids = [start_price.market_price_id, end_price.market_price_id]
    for flow in flow_report.flows:
        flow_price = _price_point(db, config, flow.transaction_date, start.base_currency)
        if flow_price is None:
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
    }
