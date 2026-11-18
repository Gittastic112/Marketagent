"""QuantStats scalar adapters and a self-contained escaped HTML report."""

import html
import math

from app.schemas.research_lab import ReportRequest
from app.services.research_lab.common import require_package
from app.services.research_lab.errors import ResearchAdapterError


def _finite(value) -> float | None:
    numeric = float(value)
    return numeric if math.isfinite(numeric) else None


def report(request: ReportRequest) -> dict:
    version = require_package("quantstats")
    import numpy as np
    import pandas as pd
    import quantstats as qs

    series = pd.Series(
        [row.return_decimal for row in request.returns],
        index=pd.to_datetime([row.date for row in request.returns]),
        dtype=float,
    )
    wealth = np.cumprod(1 + series.to_numpy())
    if not np.isfinite(wealth).all() or np.max(wealth) > 1e100:
        raise ResearchAdapterError(
            "REPORT_OVERFLOW",
            "The supplied returns produce an unrepresentable wealth path.",
        )
    # Include initial capital in drawdown: a first-period loss must not disappear.
    peak = np.maximum.accumulate(np.r_[1.0, wealth])[1:]
    drawdown = wealth / peak - 1
    annualized = -1.0 if wealth[-1] == 0 else None
    if wealth[-1] > 0:
        exponent = math.log(float(wealth[-1])) * request.periods_per_year / len(series)
        annualized = math.expm1(exponent) if exponent < 700 else None
    metrics = {
        "total_return": _finite(qs.stats.comp(series)),
        "annualized_return": annualized,
        "annualized_volatility": _finite(
            qs.stats.volatility(
                series, periods=request.periods_per_year, prepare_returns=False
            )
        ),
        # Avoid upstream price/return inference for a legitimate return above 100%.
        "sharpe_ratio": None
        if series.std() <= 1e-12
        else _finite(
            (
                series.mean()
                - ((1 + request.risk_free_rate) ** (1 / request.periods_per_year) - 1)
            )
            / series.std(ddof=1)
            * math.sqrt(request.periods_per_year)
        ),
        "max_drawdown": float(drawdown.min()),
        "win_rate": _finite(qs.stats.win_rate(series, prepare_returns=False)),
        "observation_count": len(series),
    }
    comparison = None
    if request.benchmark is not None:
        benchmark = pd.Series(
            [row.return_decimal for row in request.benchmark],
            index=series.index,
            dtype=float,
        )
        benchmark_wealth = np.cumprod(1 + benchmark.to_numpy())
        if not np.isfinite(benchmark_wealth).all():
            raise ResearchAdapterError(
                "REPORT_OVERFLOW",
                "Benchmark returns produce an unrepresentable wealth path.",
            )
        variance = float(benchmark.var(ddof=1))
        active = series - benchmark
        comparison = {
            "total_return": float(benchmark_wealth[-1] - 1),
            "beta": None
            if variance <= 1e-16
            else float(series.cov(benchmark) / variance),
            "correlation": None
            if variance <= 1e-16 or series.var() <= 1e-16
            else _finite(series.corr(benchmark)),
            "tracking_error_annualized": float(
                active.std(ddof=1) * math.sqrt(request.periods_per_year)
            ),
        }
    curve = [
        {
            "date": row.date.isoformat(),
            "wealth_index": float(wealth[index]),
            "drawdown": float(drawdown[index]),
            "return_decimal": row.return_decimal,
        }
        for index, row in enumerate(request.returns)
    ]
    return {
        "adapter": "quantstats",
        "adapter_version": version,
        "title": request.title,
        "source_label": request.source_label,
        "metrics": metrics,
        "benchmark": comparison,
        "equity_curve": curve,
        "warnings": [
            "Return inputs are user supplied; no price download or external network request is made.",
            "Annualization uses observation count and the declared periods per year.",
            "Drawdown includes initial capital; nonfinite or undefined ratios are null.",
        ],
    }


def render_html(saved: dict) -> str:
    """Only our own escaped markup, no provider templates, scripts, or remote assets."""
    result, manifest = saved["result"], saved["manifest"]
    metrics = result.get("metrics", {})
    cells = "".join(
        f"<tr><th>{html.escape(str(key))}</th><td>{html.escape(str(value) if value is not None else 'Unavailable')}</td></tr>"
        for key, value in metrics.items()
    )
    warnings = "".join(
        f"<li>{html.escape(str(warning))}</li>" for warning in saved.get("warnings", [])
    )
    curve = result.get("equity_curve", [])
    svg = ""
    if curve:
        wealth = [float(row["wealth_index"]) for row in curve]
        low, high = min(wealth + [1]), max(wealth + [1])
        span = high - low or 1
        points = " ".join(
            f"{20 + index * 760 / max(1, len(wealth) - 1):.2f},{210 - (value - low) / span * 180:.2f}"
            for index, value in enumerate(wealth)
        )
        svg = f'<svg viewBox="0 0 800 240" role="img" aria-label="Hypothetical wealth index"><polyline fill="none" stroke="#3854d9" stroke-width="2" points="{points}"/></svg>'
    return (
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
        "<title>Marketagent research report</title><style>body{font:16px system-ui;max-width:960px;margin:40px auto;padding:24px;color:#202326}"
        "td,th{padding:10px;text-align:left;border-bottom:1px solid #ddd}table{width:100%;border-collapse:collapse}code{overflow-wrap:anywhere}svg{width:100%}</style><body>"
        f"<h1>{html.escape(result.get('title', 'Marketagent research report'))}</h1>"
        f"<p>Run {int(saved['run_id'])}. Hypothetical research. Adapter {html.escape(manifest['adapter'])} {html.escape(manifest['adapter_version'])}.</p>"
        f"{svg}<table>{cells}</table><h2>Qualifications</h2><ul>{warnings}</ul>"
        f"<h2>Reproducibility</h2><p>Input SHA256 <code>{html.escape(manifest['input_sha256'])}</code></p>"
        f"<p>Output SHA256 <code>{html.escape(manifest['output_sha256'])}</code></p>"
        f"<p>Saved at {html.escape(manifest['created_at'])}. Download the JSON export for the exact inputs and manifest.</p></body></html>"
    )
