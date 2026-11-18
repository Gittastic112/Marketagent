from datetime import date

import pytest

from app.schemas.research_lab import AllocationRequest, ReportRequest, SimulationRequest
from app.services.research_lab.allocation import allocate
from app.services.research_lab.errors import ResearchAdapterError
from app.services.research_lab.reporting import report, render_html
from app.services.research_lab.simulation import simulate
from .test_research_contracts import dataset_payload


def test_minimum_variance_satisfies_group_and_turnover_constraints():
    pytest.importorskip("pypfopt")
    payload = AllocationRequest(
        dataset=dataset_payload(),
        max_weight=0.7,
        groups=[
            {
                "name": "riskier",
                "members": ["B", "C"],
                "min_weight": 0.4,
                "max_weight": 0.65,
            }
        ],
        baseline_weights={"A": 0.4, "B": 0.3, "C": 0.3},
        max_turnover=0.4,
    )
    result = allocate(payload)
    assert result["source_label"] == payload.dataset.source_label
    weights = result["weights"]
    assert sum(weights.values()) == pytest.approx(1, abs=1e-6)
    assert 0.4 - 1e-6 <= weights["B"] + weights["C"] <= 0.65 + 1e-6
    assert max(weights.values()) <= 0.7 + 1e-6
    assert result["metrics"]["gross_turnover"] <= 0.4 + 1e-6
    assert result["metrics"]["annual_expected_return"] is None
    assert result["metrics"]["sharpe_ratio"] is None


@pytest.mark.parametrize("objective", ["min_volatility", "max_sharpe", "hrp"])
def test_real_optimizer_output_is_finite_and_fully_invested(objective):
    pytest.importorskip("pypfopt")
    result = allocate(
        AllocationRequest(
            dataset=dataset_payload(),
            objective=objective,
            annual_expected_returns={"A": 0.1, "B": 0.08, "C": 0.12},
        )
    )
    assert sum(result["weights"].values()) == pytest.approx(1, abs=1e-6)
    assert min(result["weights"].values()) >= -1e-6
    assert 0 < result["metrics"]["annualized_volatility"] < 1


def test_equal_weights_cannot_silently_ignore_infeasible_group_cap():
    with pytest.raises(ResearchAdapterError, match="violates group"):
        allocate(
            AllocationRequest(
                dataset=dataset_payload(),
                objective="equal_weight",
                groups=[{"name": "small", "members": ["A"], "max_weight": 0.1}],
            )
        )


def test_return_compounding_drawdown_and_entry_cost():
    data = {
        "base_currency": "USD",
        "return_basis": "price_return",
        "source_label": "Synthetic test fixture",
        "assets": [{"key": "A", "ticker": "A", "currency": "USD"}],
        "observations": [
            {
                "start_date": "2025-01-01",
                "end_date": "2025-01-02",
                "returns": {"A": -0.5},
            },
            {"start_date": "2025-01-02", "end_date": "2025-01-03", "returns": {"A": 1}},
        ],
    }
    result = simulate(
        SimulationRequest(
            dataset=data,
            initial_weights={"A": 1},
            weight_decision_date=date(2025, 1, 1),
        )
    )
    assert result["metrics"]["total_return"] == pytest.approx(0)
    assert result["source_label"] == data["source_label"]
    assert result["metrics"]["max_drawdown"] == pytest.approx(-0.5)
    charged = simulate(
        SimulationRequest(
            dataset=data,
            initial_weights={"A": 1},
            weight_decision_date=date(2025, 1, 1),
            transaction_cost_bps=100,
        )
    )
    assert charged["metrics"]["total_return"] == pytest.approx(-0.01)
    assert charged["total_cost_in_initial_wealth_units"] == pytest.approx(0.01)
    assert charged["metrics"]["max_drawdown"] == pytest.approx(-0.505)


def test_rebalance_cannot_resurrect_an_asset_after_complete_loss():
    data = {
        "base_currency": "USD",
        "return_basis": "price_return",
        "source_label": "Synthetic terminal-loss fixture",
        "assets": [
            {"key": key, "ticker": key, "currency": "USD"} for key in ("A", "B")
        ],
        "observations": [
            {
                "start_date": "2025-01-01",
                "end_date": "2025-01-02",
                "returns": {"A": -1, "B": 0},
            },
            {
                "start_date": "2025-01-02",
                "end_date": "2025-01-03",
                "returns": {"A": 1, "B": 0},
            },
        ],
    }
    payload = SimulationRequest(
        dataset=data,
        initial_weights={"A": 0.5, "B": 0.5},
        weight_decision_date=date(2025, 1, 1),
        strategy="constant_weight",
        rebalance="each_period",
    )
    with pytest.raises(ResearchAdapterError) as error:
        simulate(payload)
    assert error.value.code == "TERMINAL_ASSET_REBALANCE"
    held = simulate(payload.model_copy(update={"strategy": "buy_and_hold"}))
    assert held["equity_curve"][-1]["wealth_index"] == pytest.approx(0.5)


@pytest.mark.parametrize(
    "strategy,rebalance",
    [
        ("buy_and_hold", "monthly"),
        ("constant_weight", "monthly"),
        ("constant_weight", "quarterly"),
        ("constant_weight", "each_period"),
    ],
)
def test_real_bt_matches_independent_native_compounding(strategy, rebalance):
    pytest.importorskip("bt")
    result = simulate(
        SimulationRequest(
            dataset=dataset_payload(),
            initial_weights={"A": 0.3, "B": 0.4, "C": 0.3},
            weight_decision_date=date(2025, 1, 1),
            strategy=strategy,
            rebalance=rebalance,
            engine="bt",
        )
    )
    assert result["cross_check"]["max_absolute_wealth_difference"] < 1e-8


def test_quantstats_adapter_handles_large_returns_without_inference_or_lost_first_loss():
    pytest.importorskip("quantstats")
    result = report(
        ReportRequest(
            source_label="Synthetic fixture",
            returns=[
                {"date": "2025-01-01", "return_decimal": -0.5},
                {"date": "2025-01-02", "return_decimal": 2},
            ],
        )
    )
    assert result["metrics"]["total_return"] == pytest.approx(0.5)
    assert result["metrics"]["max_drawdown"] == pytest.approx(-0.5)
    assert result["metrics"]["annualized_volatility"] > 10


def test_export_escapes_untrusted_titles_and_warnings():
    rendered = render_html(
        {
            "run_id": 1,
            "result": {"title": "<script>alert(1)</script>", "metrics": {"safe": 1}},
            "manifest": {
                "adapter": "test",
                "adapter_version": "1",
                "created_at": "2025-01-01",
                "input_sha256": "a" * 64,
                "output_sha256": "b" * 64,
            },
            "warnings": ["<img src=x onerror=alert(1)>"],
        }
    )
    assert "<script>" not in rendered and "<img" not in rendered
    assert "&lt;script&gt;" in rendered


def test_export_displays_benchmark_percentages_and_undefined_ratios():
    rendered = render_html({
        "run_id": 7,
        "result": {"metrics": {"total_return": 0.25}, "benchmark": {
            "total_return": 0.125, "tracking_error_annualized": 0.0,
            "beta": 1.2, "correlation": None}},
        "manifest": {"adapter": "Mock Data", "adapter_version": "1", "created_at": "2025-01-01",
                     "input_sha256": "a" * 64, "output_sha256": "b" * 64},
    })
    assert "Saved benchmark comparison" in rendered
    assert "25.00%" in rendered and "12.50%" in rendered and "0.00%" in rendered
    assert "<th scope=\"row\">beta</th><td>1.2</td>" in rendered
    assert "<th scope=\"row\">correlation</th><td>Unavailable</td>" in rendered
    assert "Ratios are unitless" in rendered
