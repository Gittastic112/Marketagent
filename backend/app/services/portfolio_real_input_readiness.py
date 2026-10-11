from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    DcfAssumptionSet,
    DcfOutput,
    FxRateObservation,
    MarketPrice,
    Portfolio,
    PortfolioBenchmarkConfig,
    PortfolioHolding,
    PortfolioSnapshot,
    ValuationModel,
)
from app.services.portfolio_benchmark import calculate_benchmark_opportunity_cost
from app.services.portfolio_risk_return import calculate_portfolio_risk_return


DEFAULT_MIN_OBSERVATIONS = 20
DEFAULT_LOOKBACK_DAYS = 365


def _has_mock_marker(value: object) -> bool:
    if value is None:
        return False
    text = str(value).strip().lower()
    return any(marker in text for marker in ("mock data", "mock_fixture", "e2e_mock"))


def _payload_has_mock_marker(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            _payload_has_mock_marker(key) or _payload_has_mock_marker(item)
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple, set)):
        return any(_payload_has_mock_marker(item) for item in value)
    return _has_mock_marker(value)


def _snapshot_is_source_labeled(snapshot: PortfolioSnapshot, foreign_holding_ids: set[int]) -> bool:
    payload = snapshot.payload_json or {}
    holdings = payload.get("holdings")
    if not isinstance(holdings, list) or not holdings:
        return False
    for holding in holdings:
        if not isinstance(holding, dict):
            return False
        if not holding.get("market_price_id") or not holding.get("market_price_provider"):
            return False
        holding_id = holding.get("holding_id")
        if holding_id in foreign_holding_ids and not holding.get("market_fx_observation_id"):
            return False
    return True


def audit_portfolio_real_input_readiness(
    db: Session,
    portfolio_id: int,
    *,
    user_id: str,
    min_observations: int = DEFAULT_MIN_OBSERVATIONS,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
) -> dict[str, Any]:
    """Audit whether persisted, non-mock inputs can support the manual portfolio smoke."""
    portfolio = db.scalar(
        select(Portfolio).where(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == user_id,
        )
    )
    if portfolio is None:
        raise ValueError("Owned portfolio not found")

    holdings = list(
        db.scalars(
            select(PortfolioHolding)
            .where(
                PortfolioHolding.portfolio_id == portfolio_id,
                PortfolioHolding.quantity > 0,
            )
            .order_by(PortfolioHolding.id)
        )
    )
    complete_snapshots = list(
        db.scalars(
            select(PortfolioSnapshot)
            .where(
                PortfolioSnapshot.portfolio_id == portfolio_id,
                PortfolioSnapshot.calculation_status == "complete",
                PortfolioSnapshot.total_portfolio_value.is_not(None),
            )
            .order_by(PortfolioSnapshot.snapshot_date, PortfolioSnapshot.id)
        )
    )
    start_date = complete_snapshots[0].snapshot_date if len(complete_snapshots) >= 2 else None
    end_date = complete_snapshots[-1].snapshot_date if len(complete_snapshots) >= 2 else None
    target_date = end_date or date.today()
    foreign_holdings = [
        holding
        for holding in holdings
        if holding.currency.upper() != portfolio.base_currency.upper()
    ]
    foreign_holding_ids = {holding.id for holding in foreign_holdings}

    risk = calculate_portfolio_risk_return(
        db,
        portfolio_id,
        target_date,
        lookback_days=lookback_days,
        min_observations=min_observations,
        user_id=user_id,
    )
    risk_by_holding = {row["holding_id"]: row for row in risk["holdings"]}
    benchmark = db.scalar(
        select(PortfolioBenchmarkConfig)
        .where(
            PortfolioBenchmarkConfig.portfolio_id == portfolio_id,
            PortfolioBenchmarkConfig.active.is_(True),
        )
        .order_by(PortfolioBenchmarkConfig.id)
    )
    benchmark_report = (
        calculate_benchmark_opportunity_cost(db, portfolio_id, start_date, end_date)
        if start_date is not None and end_date is not None
        else None
    )

    source_snapshot_ids = [snapshot.id for snapshot in complete_snapshots]
    source_market_price_ids = set(risk["source_market_price_ids"])
    source_fx_observation_ids = set(risk["source_fx_observation_ids"])
    source_dcf_output_ids = set(risk["source_dcf_output_ids"])
    if benchmark_report is not None:
        source_market_price_ids.update(benchmark_report["source_market_price_ids"])

    prices = list(
        db.scalars(
            select(MarketPrice).where(MarketPrice.id.in_(source_market_price_ids))
        )
    ) if source_market_price_ids else []
    fx_observations = list(
        db.scalars(
            select(FxRateObservation).where(FxRateObservation.id.in_(source_fx_observation_ids))
        )
    ) if source_fx_observation_ids else []
    dcf_models = list(
        db.scalars(
            select(ValuationModel)
            .join(DcfAssumptionSet, DcfAssumptionSet.valuation_model_id == ValuationModel.id)
            .join(DcfOutput, DcfOutput.assumption_set_id == DcfAssumptionSet.id)
            .where(DcfOutput.id.in_(source_dcf_output_ids))
        )
    ) if source_dcf_output_ids else []

    contains_mock_data = bool(
        risk["contains_mock_data"]
        or _has_mock_marker(portfolio.name)
        or _has_mock_marker(portfolio.description)
        or any(_payload_has_mock_marker(snapshot.payload_json) for snapshot in complete_snapshots)
        or (
            benchmark is not None
            and any(_has_mock_marker(value) for value in (benchmark.provider_name, benchmark.notes))
        )
        or any(
            _has_mock_marker(value)
            for price in prices
            for value in (price.provider_name, price.price_type, price.warnings_json)
        )
        or any(
            _has_mock_marker(value)
            for observation in fx_observations
            for value in (
                observation.provider_name,
                observation.provider_symbol,
                observation.source_url,
            )
        )
        or any(
            _has_mock_marker(value)
            for model in dcf_models
            for value in (model.name, model.description)
        )
    )

    checks: list[dict[str, Any]] = []
    blockers: list[str] = []

    def add_check(
        *,
        code: str,
        label: str,
        passed: bool,
        required: str,
        observed: str,
        blocked_message: str,
        source_record_ids: list[int] | None = None,
    ) -> None:
        message = "Requirement satisfied." if passed else blocked_message
        checks.append(
            {
                "code": code,
                "label": label,
                "status": "passed" if passed else "blocked",
                "required": required,
                "observed": observed,
                "message": message,
                "source_record_ids": source_record_ids or [],
            }
        )
        if not passed:
            blockers.append(blocked_message)

    add_check(
        code="positive_holdings",
        label="Positive holdings",
        passed=bool(holdings),
        required="At least one positive-quantity holding.",
        observed=f"{len(holdings)} positive-quantity holding(s).",
        blocked_message="Add at least one positive-quantity holding.",
        source_record_ids=[holding.id for holding in holdings],
    )
    add_check(
        code="complete_snapshot_boundaries",
        label="Complete snapshot boundaries",
        passed=len(complete_snapshots) >= 2 and start_date < end_date,
        required="At least two complete snapshots on distinct dates.",
        observed=(
            f"{len(complete_snapshots)} complete snapshot(s)"
            + (f" from {start_date} through {end_date}." if start_date and end_date else ".")
        ),
        blocked_message="Capture at least two complete point-in-time snapshots.",
        source_record_ids=source_snapshot_ids,
    )
    add_check(
        code="non_base_currency_holding",
        label="Non-base-currency exposure",
        passed=bool(foreign_holdings),
        required="At least one holding denominated outside the portfolio base currency.",
        observed=f"{len(foreign_holdings)} non-{portfolio.base_currency.upper()} holding(s).",
        blocked_message="Add at least one genuine non-base-currency holding.",
        source_record_ids=[holding.id for holding in foreign_holdings],
    )
    aligned_ready = bool(holdings) and risk["risk_calculation_status"] == "complete" and all(
        risk_by_holding.get(holding.id, {}).get("aligned_observation_count", 0) >= min_observations
        for holding in holdings
    )
    add_check(
        code="aligned_price_history",
        label="Aligned price history",
        passed=aligned_ready,
        required=f"At least {min_observations} aligned base-currency return observations per holding.",
        observed="; ".join(
            f"{holding.ticker}: {risk_by_holding.get(holding.id, {}).get('aligned_observation_count', 0)}"
            for holding in holdings
        ) or "No holding price history.",
        blocked_message=f"Provide at least {min_observations + 1} dated source-labeled prices per holding with {min_observations} aligned returns.",
        source_record_ids=sorted(risk["source_market_price_ids"]),
    )
    fx_ready = bool(foreign_holdings) and all(
        len(risk_by_holding.get(holding.id, {}).get("source_fx_observation_ids", []))
        >= min_observations + 1
        for holding in foreign_holdings
    )
    add_check(
        code="dated_fx_evidence",
        label="Dated FX evidence",
        passed=fx_ready,
        required=f"At least {min_observations + 1} dated FX observations for every non-base holding.",
        observed="; ".join(
            f"{holding.ticker}: {len(risk_by_holding.get(holding.id, {}).get('source_fx_observation_ids', []))}"
            for holding in foreign_holdings
        ) or "No non-base holding FX evidence.",
        blocked_message="Add dated source-labeled FX observations covering each non-base holding's price history.",
        source_record_ids=sorted(source_fx_observation_ids),
    )
    add_check(
        code="active_benchmark",
        label="Active benchmark",
        passed=benchmark is not None,
        required="One active, explicitly sourced portfolio benchmark.",
        observed=(
            f"{benchmark.ticker} via {benchmark.provider_name}."
            if benchmark is not None
            else "No active benchmark."
        ),
        blocked_message="Configure one active source-labeled benchmark.",
        source_record_ids=[benchmark.id] if benchmark is not None else [],
    )
    benchmark_ready = benchmark_report is not None and benchmark_report["calculation_status"] == "complete"
    add_check(
        code="benchmark_period",
        label="Benchmark period evidence",
        passed=benchmark_ready,
        required="Benchmark comparison must resolve on both snapshot boundaries.",
        observed=(
            benchmark_report["calculation_status"]
            if benchmark_report is not None
            else "Snapshot boundaries unavailable."
        ),
        blocked_message="Add benchmark prices and any required FX on both snapshot boundary dates.",
        source_record_ids=(
            sorted(benchmark_report["source_market_price_ids"])
            if benchmark_report is not None
            else []
        ),
    )
    trusted_dcf_count = sum(
        row["expected_return_decimal"] is not None and row["source_dcf_output_id"] is not None
        for row in risk["holdings"]
    )
    add_check(
        code="trusted_base_dcf",
        label="Trusted Base DCF",
        passed=trusted_dcf_count >= 1,
        required="At least one non-stale, quality-gated Base DCF output with matching currency.",
        observed=f"{trusted_dcf_count} trusted Base DCF output(s).",
        blocked_message="Complete at least one trusted Base DCF output for a held company.",
        source_record_ids=sorted(source_dcf_output_ids),
    )
    source_labels_ready = bool(prices) and all(
        bool(price.provider_name and price.price_type) for price in prices
    ) and bool(fx_observations) and all(
        bool(observation.provider_name and (observation.provider_symbol or observation.source_url))
        for observation in fx_observations
    ) and benchmark is not None and bool(
        benchmark.provider_name and (benchmark.provider_symbol or benchmark.notes)
    ) and bool(complete_snapshots) and all(
        _snapshot_is_source_labeled(snapshot, foreign_holding_ids)
        for snapshot in complete_snapshots
    )
    add_check(
        code="source_labels",
        label="Source labels and record links",
        passed=source_labels_ready,
        required="Prices, FX, benchmark, and snapshots must retain explicit source labels and record IDs.",
        observed=(
            f"{len(prices)} price, {len(fx_observations)} FX, "
            f"{len(complete_snapshots)} snapshot record(s)."
        ),
        blocked_message="Add explicit provider labels and source record links to every required input.",
        source_record_ids=sorted(
            set(source_snapshot_ids)
            | source_market_price_ids
            | source_fx_observation_ids
            | source_dcf_output_ids
        ),
    )
    add_check(
        code="no_mock_data",
        label="No Mock Data",
        passed=not contains_mock_data,
        required="No required record may be labeled or detected as Mock Data.",
        observed="Mock Data detected." if contains_mock_data else "No Mock Data markers detected.",
        blocked_message="Mock Data is present; replace it with genuine source-labeled inputs before certification.",
    )

    warnings = sorted(
        set(
            [*risk["warnings"]]
            + (
                list(benchmark_report["warnings"])
                if benchmark_report is not None
                else []
            )
        )
    )
    return {
        "portfolio_id": portfolio.id,
        "user_id": portfolio.user_id,
        "certification_status": "ready" if not blockers else "blocked",
        "claim_type": "Calculation",
        "as_of_date": target_date,
        "start_date": start_date,
        "end_date": end_date,
        "lookback_days": lookback_days,
        "min_observations": min_observations,
        "contains_mock_data": contains_mock_data,
        "checks": checks,
        "blockers": blockers,
        "warnings": warnings,
        "source_snapshot_ids": source_snapshot_ids,
        "source_market_price_ids": sorted(source_market_price_ids),
        "source_fx_observation_ids": sorted(source_fx_observation_ids),
        "source_dcf_output_ids": sorted(source_dcf_output_ids),
    }
