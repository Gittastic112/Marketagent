"""Explicit long-only research simulations, with an optional bt cross-check."""

import math

from app.schemas.research_lab import SimulationRequest
from app.services.research_lab.common import require_package
from app.services.research_lab.errors import ResearchAdapterError


def _bucket(day, frequency: str):
    if frequency == "monthly":
        return day.year, day.month
    if frequency == "quarterly":
        return day.year, (day.month - 1) // 3
    if frequency == "yearly":
        return day.year
    return day


def rebalance_indices(request: SimulationRequest) -> list[int]:
    """Decisions occur at interval starts, before that interval's return."""
    result = [0]
    if request.strategy == "constant_weight":
        starts = [row.start_date for row in request.dataset.observations]
        result.extend(
            index
            for index in range(1, len(starts))
            if _bucket(starts[index], request.rebalance)
            != _bucket(starts[index - 1], request.rebalance)
        )
    return result


def _summary(curve: list[dict], periods: int) -> dict:
    import numpy as np

    values = np.array([row["return_decimal"] for row in curve], dtype=float)
    wealth = curve[-1]["wealth_index"]
    annualized = None
    if wealth == 0:
        annualized = -1.0
    elif wealth > 0:
        exponent = math.log(wealth) * periods / len(values)
        annualized = math.expm1(exponent) if exponent < 700 else None
    return {
        "total_return": wealth - 1,
        "annualized_return": annualized,
        "annualized_volatility": float(values.std(ddof=1) * math.sqrt(periods)),
        "max_drawdown": min(row["drawdown"] for row in curve),
        "observation_count": len(curve),
    }


def simulate(request: SimulationRequest) -> dict:
    keys = [asset.key for asset in request.dataset.assets]
    target = {key: float(request.initial_weights[key]) for key in keys}
    weights = {key: 0.0 for key in keys}  # Initially cash, initial entry is charged.
    wealth, peak, cost_sum, turnover_sum = 1.0, 1.0, 0.0, 0.0
    curve, rebalances = [], []
    rebalance_at = set(rebalance_indices(request))
    terminal_assets: set[str] = set()
    cost_rate = request.transaction_cost_bps / 10_000
    for index, row in enumerate(request.dataset.observations):
        before = wealth
        if index in rebalance_at and wealth > 0:
            if any(target[key] > 0 for key in terminal_assets):
                raise ResearchAdapterError(
                    "TERMINAL_ASSET_REBALANCE",
                    "A rebalance would buy an asset after a complete loss. Supply explicit asset-exit handling or use buy-and-hold.",
                )
            turnover = sum(abs(target[key] - weights[key]) for key in keys)
            cost = wealth * turnover * cost_rate
            wealth -= cost
            cost_sum += cost
            turnover_sum += turnover
            weights = target.copy()
            rebalances.append(
                {
                    "date": row.start_date.isoformat(),
                    "gross_turnover": turnover,
                    "cost_in_initial_wealth_units": cost,
                    "target_weights": target,
                }
            )
        gross_factor = sum(weights[key] * (1 + float(row.returns[key])) for key in keys)
        wealth *= gross_factor
        if not math.isfinite(wealth) or wealth > 1e100:
            raise ResearchAdapterError(
                "SIMULATION_OVERFLOW",
                "The supplied returns produce an unrepresentable wealth path.",
            )
        if gross_factor > 0:
            weights = {
                key: weights[key] * (1 + row.returns[key]) / gross_factor
                for key in keys
            }
        else:
            weights = {key: 0.0 for key in keys}
        terminal_assets.update(key for key in keys if row.returns[key] == -1)
        peak = max(peak, wealth)
        curve.append(
            {
                "date": row.end_date.isoformat(),
                "wealth_index": wealth,
                "return_decimal": wealth / before - 1 if before else 0.0,
                "drawdown": wealth / peak - 1,
            }
        )
    adapter, version = "native_research_simulation", "1"
    cross_check = None
    if request.engine == "bt":
        version = require_package("bt")
        bt_curve = _bt_wealth(request, rebalance_at)
        error = max(
            abs(expected["wealth_index"] - actual)
            for expected, actual in zip(curve, bt_curve, strict=True)
        )
        if error > 1e-7:
            raise ResearchAdapterError(
                "BT_RECONCILIATION_FAILED",
                "bt did not reconcile to the explicit zero-cost simulation.",
                502,
            )
        adapter = "bt"
        cross_check = {
            "engine": "native_research_simulation",
            "max_absolute_wealth_difference": error,
        }
    warnings = [
        "Hypothetical fixed-universe simulation, not realized portfolio performance or a trade instruction.",
        "Weight decision date is caller-supplied; input data and universe selection are not verified point-in-time.",
        "Annualization uses the declared periods_per_year, not a verified exchange calendar.",
    ]
    if request.dataset.return_basis == "price_return":
        warnings.append(
            "The simulation uses price returns; distributions, taxes, and financing are excluded."
        )
    if cost_sum:
        warnings.append(
            "Costs use pretrade NAV times gross weight turnover; this is an explicit proportional cost estimate."
        )
    return {
        "adapter": adapter,
        "adapter_version": version,
        "metrics": _summary(curve, request.dataset.periods_per_year),
        "equity_curve": curve,
        "final_weights": weights,
        "rebalances": rebalances,
        "gross_turnover": turnover_sum,
        "total_cost_in_initial_wealth_units": cost_sum,
        "cost_model": "pretrade_nav_times_sum_absolute_weight_changes_including_entry",
        "cross_check": cross_check,
        "base_currency": request.dataset.base_currency,
        "source_label": request.dataset.source_label,
        "return_basis": request.dataset.return_basis,
        "warnings": warnings,
    }


def _bt_wealth(request: SimulationRequest, rebalance_at: set[int]) -> list[float]:
    import bt
    import pandas as pd

    rows = request.dataset.observations
    keys = [asset.key for asset in request.dataset.assets]
    # A baseline point permits entry before the first return. No remote bt.get().
    dates = pd.to_datetime([rows[0].start_date, *[row.end_date for row in rows]])
    prices = {key: [100.0] for key in keys}
    for row in rows:
        for key in keys:
            prices[key].append(prices[key][-1] * (1 + row.returns[key]))
    frame = pd.DataFrame(prices, index=dates)
    decisions = pd.DataFrame(
        {key: [request.initial_weights[key] for _ in rebalance_at] for key in keys},
        index=pd.to_datetime(
            [rows[index].start_date for index in sorted(rebalance_at)]
        ),
    )
    strategy = bt.Strategy(
        "marketagent_research", [bt.algos.WeighTarget(decisions), bt.algos.Rebalance()]
    )
    test = bt.Backtest(
        strategy,
        frame,
        integer_positions=False,
        initial_capital=1_000_000,
        commissions=lambda quantity, price: 0,
        progress_bar=False,
    )
    test.run()
    series = test.strategy.prices.reindex(dates)
    if series.isna().any() or float(series.iloc[0]) <= 0:
        raise ResearchAdapterError(
            "BT_INVALID_RESULT", "bt returned incomplete simulation dates.", 502
        )
    baseline = float(series.iloc[0])
    return [float(value) / baseline for value in series.iloc[1:]]
