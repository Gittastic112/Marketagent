from __future__ import annotations
from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator


PEER_MULTIPLE_METHODS = (
    "pe",
    "pbv",
    "ps",
    "ev_sales",
    "ev_ebitda",
    "ev_ebit",
)


MAXIMUM_PEER_MEMBERS = 50


class PeerMultiplesInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pe: float | None = Field(default=None, gt=0, le=1000)
    pbv: float | None = Field(default=None, gt=0, le=1000)
    ps: float | None = Field(default=None, gt=0, le=1000)
    ev_sales: float | None = Field(default=None, gt=0, le=1000)
    ev_ebitda: float | None = Field(default=None, gt=0, le=1000)
    ev_ebit: float | None = Field(default=None, gt=0, le=1000)

    @model_validator(mode="after")
    def require_at_least_one_multiple(self) -> "PeerMultiplesInput":
        if not any(getattr(self, method) is not None for method in PEER_MULTIPLE_METHODS):
            raise ValueError("At least one positive peer multiple is required")
        return self


class PeerMemberInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identifier: str = Field(min_length=1, max_length=80)
    companyId: int | None = Field(default=None, ge=1)
    name: str | None = Field(default=None, max_length=160)
    included: bool = True
    multiples: PeerMultiplesInput
    sourceName: str = Field(min_length=1, max_length=160)
    sourceUrl: HttpUrl
    sourceAsOf: date
    claimType: Literal["Fact", "Source Summary"] = "Fact"
    notes: str | None = Field(default=None, max_length=1000)
    country: str | None = Field(default=None, max_length=120)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    fiscalPeriodEnd: date | None = None
    accountingStandard: Literal["IFRS", "US GAAP", "IND AS", "OTHER"] | None = None
    marketCap: float | None = Field(default=None, gt=0, le=1_000_000_000_000_000)
    revenueGrowthPct: float | None = Field(default=None, ge=-100, le=1000)
    ebitdaMarginPct: float | None = Field(default=None, ge=-1000, le=100)

    @field_validator("identifier")
    @classmethod
    def normalize_identifier(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("Peer identifier is required")
        return normalized

    @field_validator("sourceName")
    @classmethod
    def reject_mock_source(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Source name is required")
        if "mock" in normalized.casefold():
            raise ValueError("Mock Data cannot be used as peer evidence")
        return normalized

    @field_validator("sourceAsOf")
    @classmethod
    def reject_future_source_date(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("Peer source date cannot be in the future")
        return value

    @field_validator("country")
    @classmethod
    def normalize_country(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if not normalized.isalpha():
            raise ValueError("Peer currency must be a three-letter alphabetic code")
        return normalized

    @model_validator(mode="after")
    def validate_comparability_dates(self) -> "PeerMemberInput":
        if self.fiscalPeriodEnd and self.fiscalPeriodEnd > self.sourceAsOf:
            raise ValueError("Fiscal period end cannot be after the peer source date")
        return self


class PeerTargetContextInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sourceName: str = Field(min_length=1, max_length=160)
    sourceUrl: HttpUrl
    sourceAsOf: date
    claimType: Literal["Fact", "Source Summary"] = "Fact"
    notes: str | None = Field(default=None, max_length=1000)
    country: str | None = Field(default=None, max_length=120)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    fiscalPeriodEnd: date | None = None
    accountingStandard: Literal["IFRS", "US GAAP", "IND AS", "OTHER"] | None = None
    marketCap: float | None = Field(default=None, gt=0, le=1_000_000_000_000_000)
    revenueGrowthPct: float | None = Field(default=None, ge=-100, le=1000)
    ebitdaMarginPct: float | None = Field(default=None, ge=-1000, le=100)

    @field_validator("sourceName")
    @classmethod
    def reject_mock_source(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Source name is required")
        if "mock" in normalized.casefold():
            raise ValueError("Mock Data cannot be used as target-company evidence")
        return normalized

    @field_validator("sourceAsOf")
    @classmethod
    def reject_future_source_date(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("Target-company source date cannot be in the future")
        return value

    @field_validator("country")
    @classmethod
    def normalize_country(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().upper()
        if not normalized.isalpha():
            raise ValueError("Target-company currency must be a three-letter alphabetic code")
        return normalized

    @model_validator(mode="after")
    def validate_context(self) -> "PeerTargetContextInput":
        if self.fiscalPeriodEnd and self.fiscalPeriodEnd > self.sourceAsOf:
            raise ValueError("Target-company fiscal period end cannot be after its source date")
        fields = (
            self.country,
            self.currency,
            self.fiscalPeriodEnd,
            self.accountingStandard,
            self.marketCap,
            self.revenueGrowthPct,
            self.ebitdaMarginPct,
        )
        if not any(value is not None for value in fields):
            raise ValueError("Target context must contain at least one comparability fact")
        return self


class PeerValuationSetCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    companyId: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=120)
    notes: str | None = Field(default=None, max_length=4000)
    targetContext: PeerTargetContextInput | None = None
    members: list[PeerMemberInput] = Field(min_length=1, max_length=MAXIMUM_PEER_MEMBERS)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Peer-set name is required")
        return normalized


class PeerValuationSetUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expectedVersion: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=1, max_length=120)
    notes: str | None = Field(default=None, max_length=4000)
    targetContext: PeerTargetContextInput | None = None
    members: list[PeerMemberInput] | None = Field(
        default=None,
        min_length=1,
        max_length=MAXIMUM_PEER_MEMBERS,
    )

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("Peer-set name is required")
        return value.strip() if value is not None else None

    @model_validator(mode="after")
    def require_mutation(self) -> "PeerValuationSetUpdate":
        if not (self.model_fields_set & {"name", "notes", "targetContext", "members"}):
            raise ValueError("At least one peer-set field must be supplied")
        return self


class PeerValuationSetReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    acknowledged: bool
    expectedVersion: int = Field(ge=1)
    expectedDiagnosticsSha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    acknowledgedWarningCodes: list[str] = Field(default_factory=list, max_length=100)

    @field_validator("acknowledgedWarningCodes")
    @classmethod
    def normalize_warning_codes(cls, value: list[str]) -> list[str]:
        normalized = sorted({item.strip() for item in value if item.strip()})
        if len(normalized) != len(value):
            raise ValueError("Acknowledged warning codes must be unique and non-empty")
        return normalized


class PeerValuationSetMutation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expectedVersion: int = Field(ge=1)
