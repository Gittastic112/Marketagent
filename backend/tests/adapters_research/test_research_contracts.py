from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.schemas.research_lab import (
    AllocationRequest,
    ResearchDataset,
    SimulationRequest,
    ReportRequest,
)


def dataset_payload(count=80):
    start = date(2025, 1, 1)
    return {
        "base_currency": "USD",
        "return_basis": "price_return",
        "source_label": "Synthetic test fixture",
        "assets": [
            {"key": key, "ticker": key, "currency": "USD"} for key in ("A", "B", "C")
        ],
        "observations": [
            {
                "start_date": (start + timedelta(days=i)).isoformat(),
                "end_date": (start + timedelta(days=i + 1)).isoformat(),
                "returns": {
                    "A": 0.001 + (i % 5 - 2) * 0.005,
                    "B": 0.001 + (i % 7 - 3) * 0.01,
                    "C": 0.001 + (i % 3 - 1) * 0.02,
                },
            }
            for i in range(count)
        ],
    }


@pytest.mark.parametrize(
    "mutate",
    [
        lambda data: data["observations"][0]["returns"].pop("B"),
        lambda data: data["observations"][0]["returns"].update(A=float("nan")),
        lambda data: data["observations"][0]["returns"].update(A=-1.01),
        lambda data: data["observations"][1].update(start_date="2025-01-01"),
        lambda data: data["observations"][0].update(end_date="2024-12-31"),
        lambda data: data["assets"][1].update(key="A"),
        lambda data: data["assets"][0].update(currency="INR"),
    ],
)
def test_incomplete_or_ambiguous_return_inputs_are_rejected(mutate):
    data = dataset_payload()
    mutate(data)
    with pytest.raises(ValidationError):
        ResearchDataset.model_validate(data)


def test_expected_returns_must_be_explicit_and_cover_every_asset():
    with pytest.raises(ValidationError, match="annual expected returns"):
        AllocationRequest(dataset=dataset_payload(), objective="max_sharpe")
    with pytest.raises(ValidationError, match="exactly"):
        AllocationRequest(dataset=dataset_payload(), annual_expected_returns={"A": 0.1})


@pytest.mark.parametrize(
    "options",
    [
        {"min_weight": 0.4},
        {"max_weight": 0.3},
        {"max_turnover": 0.2},
        {"objective": "hrp", "max_weight": 0.8},
        {"groups": [{"name": "invalid", "members": ["UNKNOWN"]}]},
    ],
)
def test_incoherent_allocation_constraints_fail_before_execution(options):
    with pytest.raises(ValidationError):
        AllocationRequest(dataset=dataset_payload(), **options)


def test_future_weight_decisions_and_uncovered_weights_are_rejected():
    with pytest.raises(ValidationError, match="first interval"):
        SimulationRequest(
            dataset=dataset_payload(),
            initial_weights={"A": 0.2, "B": 0.3, "C": 0.5},
            weight_decision_date=date(2026, 1, 1),
        )
    with pytest.raises(ValidationError, match="sum to one"):
        SimulationRequest(
            dataset=dataset_payload(),
            initial_weights={"A": 0.2, "B": 0.3, "C": 0.4},
            weight_decision_date=date(2025, 1, 1),
        )


def test_report_rejects_silent_benchmark_alignment():
    with pytest.raises(ValidationError, match="exactly"):
        ReportRequest(
            source_label="Synthetic fixture",
            returns=[
                {"date": "2025-01-01", "return_decimal": 0.1},
                {"date": "2025-01-02", "return_decimal": 0.2},
            ],
            benchmark=[
                {"date": "2025-01-02", "return_decimal": 0.1},
                {"date": "2025-01-03", "return_decimal": 0.2},
            ],
        )
