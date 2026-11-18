"""Bounded research contracts; no providers, persistence, or HTTP imports."""

from datetime import date, datetime
from math import isclose
from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator


AssetKey = Annotated[
    str, Field(min_length=1, max_length=40, pattern=r"^[A-Za-z0-9_.:^/=-]+$")
]
Currency = Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
Weight = Annotated[FiniteFloat, Field(ge=0, le=1)]
SimpleReturn = Annotated[FiniteFloat, Field(ge=-1, le=100)]


class ResearchContract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ResearchAsset(ResearchContract):
    key: AssetKey
    ticker: str = Field(min_length=1, max_length=40)
    currency: Currency


class ReturnObservation(ResearchContract):
    start_date: date
    end_date: date
    returns: dict[AssetKey, SimpleReturn] = Field(min_length=1, max_length=40)

    @model_validator(mode="after")
    def positive_interval(self) -> Self:
        if self.end_date <= self.start_date:
            raise ValueError("Each return must have end_date after start_date.")
        return self


class ResearchDataset(ResearchContract):
    base_currency: Currency
    periods_per_year: int = Field(default=252, ge=1, le=366)
    return_basis: Literal["price_return", "total_return"]
    source_label: str = Field(min_length=3, max_length=300)
    assets: list[ResearchAsset] = Field(min_length=1, max_length=40)
    observations: list[ReturnObservation] = Field(min_length=2, max_length=2600)

    @model_validator(mode="after")
    def aligned_complete_matrix(self) -> Self:
        keys = [asset.key for asset in self.assets]
        if len(keys) != len(set(keys)):
            raise ValueError(
                "Asset keys must be unique, including listing identity when needed."
            )
        if any(asset.currency != self.base_currency for asset in self.assets):
            raise ValueError(
                "All input returns must already be in base_currency; implicit FX conversion is not allowed."
            )
        expected = set(keys)
        previous: ReturnObservation | None = None
        for row in self.observations:
            if set(row.returns) != expected:
                raise ValueError(
                    "Every interval must contain exactly every asset; missing returns are not filled."
                )
            if previous is not None and row.start_date != previous.end_date:
                raise ValueError(
                    "Return intervals must be ordered and contiguous, with identical boundaries for all assets."
                )
            previous = row
        return self


class GroupConstraint(ResearchContract):
    name: str = Field(min_length=1, max_length=80)
    members: list[AssetKey] = Field(min_length=1, max_length=40)
    min_weight: Weight = 0
    max_weight: Weight = 1

    @model_validator(mode="after")
    def valid_bounds(self) -> Self:
        if self.min_weight > self.max_weight or len(self.members) != len(
            set(self.members)
        ):
            raise ValueError("Group bounds must be ordered and members unique.")
        return self


class AllocationRequest(ResearchContract):
    dataset: ResearchDataset
    objective: Literal["min_volatility", "max_sharpe", "hrp", "equal_weight"] = (
        "min_volatility"
    )
    covariance: Literal["ledoit_wolf", "sample"] = "ledoit_wolf"
    min_weight: Weight = 0
    max_weight: Weight = 1
    risk_free_rate: Annotated[FiniteFloat, Field(gt=-1, le=1)] = 0.04
    annual_expected_returns: (
        dict[AssetKey, Annotated[FiniteFloat, Field(gt=-1, le=10)]] | None
    ) = None
    groups: list[GroupConstraint] = Field(default_factory=list, max_length=20)
    baseline_weights: dict[AssetKey, Weight] | None = None
    max_turnover: Annotated[FiniteFloat, Field(ge=0, le=2)] | None = None

    @model_validator(mode="after")
    def coherent_constraints(self) -> Self:
        keys = {asset.key for asset in self.dataset.assets}
        count = len(keys)
        if count < 2 or len(self.dataset.observations) < max(20, count + 1):
            raise ValueError(
                "Allocation requires at least two assets and max(20, asset_count + 1) aligned observations."
            )
        if self.min_weight * count > 1 + 1e-9 or self.max_weight * count < 1 - 1e-9:
            raise ValueError("Weight bounds cannot produce a fully invested portfolio.")
        if self.min_weight > self.max_weight:
            raise ValueError("min_weight must not exceed max_weight.")
        if (
            self.annual_expected_returns is not None
            and set(self.annual_expected_returns) != keys
        ):
            raise ValueError(
                "Expected returns must cover exactly the input asset keys."
            )
        if self.objective == "max_sharpe" and self.annual_expected_returns is None:
            raise ValueError(
                "max_sharpe requires explicit annual expected returns; DCF upside is not an annual return forecast."
            )
        for group in self.groups:
            if not set(group.members) <= keys:
                raise ValueError("Group members must exist in the dataset.")
        if self.baseline_weights is not None:
            _check_weights(self.baseline_weights, keys)
        if self.max_turnover is not None and self.baseline_weights is None:
            raise ValueError("max_turnover requires baseline_weights.")
        if self.objective in {"hrp", "max_sharpe"} and self.max_turnover is not None:
            raise ValueError(
                "Turnover constraints are supported by min_volatility and equal_weight only."
            )
        if self.objective == "hrp" and (
            self.groups or self.min_weight != 0 or self.max_weight != 1
        ):
            raise ValueError(
                "HRP does not support bounds or group constraints in this adapter."
            )
        return self


def _check_weights(weights: dict[str, float], keys: set[str]) -> None:
    if set(weights) != keys or not isclose(sum(weights.values()), 1, abs_tol=1e-8):
        raise ValueError("Weights must cover exactly all assets and sum to one.")


class SimulationRequest(ResearchContract):
    dataset: ResearchDataset
    initial_weights: dict[AssetKey, Weight] = Field(min_length=1, max_length=40)
    strategy: Literal["buy_and_hold", "constant_weight"] = "buy_and_hold"
    rebalance: Literal["monthly", "quarterly", "yearly", "each_period"] = "monthly"
    weight_decision_date: date
    transaction_cost_bps: Annotated[FiniteFloat, Field(ge=0, le=1000)] = 0
    engine: Literal["native", "bt"] = "native"

    @model_validator(mode="after")
    def valid_simulation(self) -> Self:
        _check_weights(
            self.initial_weights, {asset.key for asset in self.dataset.assets}
        )
        if self.weight_decision_date > self.dataset.observations[0].start_date:
            raise ValueError(
                "Weights must be decided no later than the first interval's start date."
            )
        if self.engine == "bt" and self.transaction_cost_bps != 0:
            raise ValueError(
                "The bt cross-check supports zero costs; use native for the explicit turnover cost model."
            )
        if self.engine == "bt" and any(
            value <= -1
            for row in self.dataset.observations
            for value in row.returns.values()
        ):
            raise ValueError(
                "bt synthetic price inputs must remain positive; native supports complete loss."
            )
        return self


class ReportObservation(ResearchContract):
    date: date
    return_decimal: SimpleReturn


class ReportRequest(ResearchContract):
    returns: list[ReportObservation] = Field(min_length=2, max_length=2600)
    benchmark: list[ReportObservation] | None = Field(
        default=None, min_length=2, max_length=2600
    )
    periods_per_year: int = Field(default=252, ge=1, le=366)
    risk_free_rate: Annotated[FiniteFloat, Field(gt=-1, le=1)] = 0.04
    title: str = Field(default="Research return report", min_length=1, max_length=120)
    source_label: str = Field(min_length=3, max_length=300)

    @model_validator(mode="after")
    def chronological_report(self) -> Self:
        dates = [row.date for row in self.returns]
        if dates != sorted(set(dates)):
            raise ValueError("Report dates must be strictly increasing and unique.")
        if self.benchmark is not None and [row.date for row in self.benchmark] != dates:
            raise ValueError(
                "Benchmark must have exactly the same ordered observation dates; no silent alignment or filling."
            )
        return self


class PeerDiscoveryRequest(ResearchContract):
    country: str | None = Field(default=None, min_length=1, max_length=100)
    sector: str | None = Field(default=None, min_length=1, max_length=100)
    industry: str | None = Field(default=None, min_length=1, max_length=120)
    query: str | None = Field(default=None, min_length=2, max_length=100)
    limit: int = Field(default=50, ge=1, le=100)


class AdapterCapability(ResearchContract):
    id: str
    label: str
    available: bool
    version: str | None = None
    reason: str | None = None


class ResearchCapabilities(ResearchContract):
    adapters: list[AdapterCapability]
    limits: dict[str, int]
    warnings: list[str] = Field(default_factory=list)


class ResearchRunManifest(ResearchContract):
    schema_version: Literal["research-lab/v1"] = "research-lab/v1"
    input_sha256: str
    output_sha256: str
    created_at: datetime
    adapter: str
    adapter_version: str
    dependencies: dict[str, str]
    source_assertion: Literal["user_supplied_unverified", "pinned_reference_snapshot"]
    valuation_as_of: date | None = None
    public_information_cutoff: datetime | None = None
    application_observed_cutoff: datetime | None = None
    snapshot_created_at: datetime
    knowledge_policy: Literal["unverified_research", "reference_snapshot"]
    deterministic_seed: int = 0


class ResearchRunResult(ResearchContract):
    run_id: int
    kind: Literal["allocation", "simulation", "report", "peers"]
    status: Literal["complete"] = "complete"
    manifest: ResearchRunManifest
    result: dict[str, Any]
    warnings: list[str] = Field(default_factory=list)


class ResearchRunSummary(ResearchContract):
    run_id: int
    kind: str
    status: str
    created_at: datetime
    input_sha256: str | None = None
    adapter: str | None = None
