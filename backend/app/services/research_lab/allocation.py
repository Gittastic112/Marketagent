"""PyPortfolioOpt behind a complete, explicitly scaled return matrix."""

import math

from app.schemas.research_lab import AllocationRequest
from app.services.research_lab.common import require_package
from app.services.research_lab.errors import ResearchAdapterError


def allocate(request: AllocationRequest) -> dict:
    import numpy as np
    import pandas as pd

    dataset = request.dataset
    keys = [asset.key for asset in dataset.assets]
    frame = pd.DataFrame(
        [row.returns for row in dataset.observations],
        columns=keys,
        index=pd.to_datetime([row.end_date for row in dataset.observations]),
    )
    warnings = [
        "Allocation is an estimate from the supplied return window, not a trade instruction.",
        "Input provenance and point-in-time availability are user assertions, not independently verified.",
    ]
    expected = (
        None
        if request.annual_expected_returns is None
        else pd.Series(request.annual_expected_returns).reindex(keys)
    )
    covariance = frame.cov() * dataset.periods_per_year
    adapter, version = "native_equal_weight", "1"
    if request.objective == "equal_weight":
        weights = {key: 1 / len(keys) for key in keys}
        covariance_method = "sample"
    else:
        version = require_package("PyPortfolioOpt")
        from pypfopt import EfficientFrontier, HRPOpt, risk_models

        adapter = "PyPortfolioOpt"
        covariance_method = request.covariance
        if request.covariance == "ledoit_wolf":
            covariance = risk_models.CovarianceShrinkage(
                frame, returns_data=True, frequency=dataset.periods_per_year
            ).ledoit_wolf()
        if float(np.max(np.diag(covariance))) <= 1e-16:
            raise ResearchAdapterError(
                "DEGENERATE_RETURNS", "The return matrix has no measurable variance."
            )
        try:
            if request.objective == "hrp":
                if (frame.std() <= 1e-12).any():
                    raise ResearchAdapterError(
                        "DEGENERATE_RETURNS",
                        "HRP requires nonconstant returns for every asset.",
                    )
                weights = dict(HRPOpt(returns=frame).optimize(linkage_method="single"))
                covariance_method = "sample"
                covariance = frame.cov() * dataset.periods_per_year
            else:
                ef = EfficientFrontier(
                    expected,
                    covariance,
                    weight_bounds=(request.min_weight, request.max_weight),
                    solver="CLARABEL",
                    solver_options={"max_iter": 200},
                )
                for group in request.groups:
                    indices = [keys.index(key) for key in group.members]
                    ef.add_constraint(
                        lambda w, indices=indices, bound=group.min_weight: w[
                            indices
                        ].sum()
                        >= bound
                    )
                    ef.add_constraint(
                        lambda w, indices=indices, bound=group.max_weight: w[
                            indices
                        ].sum()
                        <= bound
                    )
                if request.max_turnover is not None:
                    import cvxpy as cp

                    baseline = np.array([request.baseline_weights[key] for key in keys])
                    ef.add_constraint(
                        lambda w: cp.norm1(w - baseline) <= request.max_turnover
                    )
                if request.objective == "max_sharpe":
                    if float(expected.max()) <= request.risk_free_rate:
                        raise ResearchAdapterError(
                            "INFEASIBLE_EXPECTED_RETURNS",
                            "At least one expected return must exceed the risk-free rate.",
                        )
                    ef.max_sharpe(risk_free_rate=request.risk_free_rate)
                else:
                    ef.min_volatility()
                # Preserve solver precision. clean_weights() rounds and may break bounds.
                weights = {
                    key: float(ef.weights[index]) for index, key in enumerate(keys)
                }
        except ResearchAdapterError:
            raise
        except Exception as exc:
            raise ResearchAdapterError(
                "ALLOCATION_INFEASIBLE",
                "The optimizer could not satisfy these inputs and constraints.",
            ) from exc
    values = np.array([weights[key] for key in keys], dtype=float)
    tolerance = 1e-6
    if (
        not np.isfinite(values).all()
        or abs(float(values.sum()) - 1) > tolerance
        or values.min() < request.min_weight - tolerance
        or values.max() > request.max_weight + tolerance
    ):
        raise ResearchAdapterError(
            "ALLOCATION_INVALID",
            "Computed weights do not satisfy the requested constraints.",
        )
    for group in request.groups:
        actual = sum(weights[key] for key in group.members)
        if (
            actual < group.min_weight - tolerance
            or actual > group.max_weight + tolerance
        ):
            raise ResearchAdapterError(
                "ALLOCATION_INFEASIBLE", f"The allocation violates group {group.name}."
            )
    turnover = (
        None
        if request.baseline_weights is None
        else sum(abs(weights[key] - request.baseline_weights[key]) for key in keys)
    )
    if request.max_turnover is not None and turnover > request.max_turnover + tolerance:
        raise ResearchAdapterError(
            "ALLOCATION_INFEASIBLE", "The allocation exceeds the turnover constraint."
        )
    volatility = math.sqrt(max(0, float(values @ covariance.to_numpy() @ values)))
    annual_return = None if expected is None else float(values @ expected.to_numpy())
    sharpe = (
        None
        if annual_return is None or volatility <= 1e-12
        else (annual_return - request.risk_free_rate) / volatility
    )
    if len(frame) < 60:
        warnings.append(
            "Fewer than 60 aligned observations makes the risk estimate especially unstable."
        )
    if dataset.return_basis == "price_return":
        warnings.append(
            "Price returns exclude distributions unless the caller already included them; split adjustment alone is not total return."
        )
    return {
        "adapter": adapter,
        "adapter_version": version,
        "weights": weights,
        "metrics": {
            "annualized_volatility": volatility,
            "annual_expected_return": annual_return,
            "sharpe_ratio": sharpe,
            "gross_turnover": turnover,
        },
        "objective": request.objective,
        "covariance_method": covariance_method,
        "base_currency": dataset.base_currency,
        "source_label": dataset.source_label,
        "return_basis": dataset.return_basis,
        "observation_count": len(frame),
        "window_start": dataset.observations[0].start_date.isoformat(),
        "window_end": dataset.observations[-1].end_date.isoformat(),
        "warnings": warnings,
    }
