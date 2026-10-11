from __future__ import annotations

from datetime import UTC, date, datetime
from hashlib import sha256
import json
from math import isfinite
from statistics import median
from typing import Any, Literal

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Company,
    PeerValuationMemberRecord,
    PeerValuationRevisionMemberRecord,
    PeerValuationRevisionTargetProfile,
    PeerValuationSet,
    PeerValuationSetRevision,
    PeerValuationTargetProfile,
)


PEER_MULTIPLE_METHODS = (
    "pe",
    "pbv",
    "ps",
    "ev_sales",
    "ev_ebitda",
    "ev_ebit",
)
MINIMUM_METHOD_PEERS = 3
MAXIMUM_PEER_MEMBERS = 50
PEER_SOURCE_STALE_DAYS = 120
PEER_SOURCE_DATE_SPAN_WARNING_DAYS = 45
PEER_MULTIPLE_RATIO_WARNING = 3.0
PEER_RELATIVE_MAD_WARNING = 0.5
PEER_FISCAL_PERIOD_SPAN_WARNING_DAYS = 120
PEER_MARKET_CAP_RATIO_WARNING = 10.0
PEER_GROWTH_SPAN_WARNING_PCT = 20.0
PEER_MARGIN_SPAN_WARNING_PCT = 15.0


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


def _member_dict(member: PeerMemberInput) -> dict[str, Any]:
    return member.model_dump(mode="json", exclude_none=True)


def _target_dict(target: PeerTargetContextInput | None) -> dict[str, Any]:
    return target.model_dump(mode="json", exclude_none=True) if target else {}


def _target_record_kwargs(target: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_name": target["sourceName"],
        "source_url": target["sourceUrl"],
        "source_as_of": _source_date(target["sourceAsOf"]),
        "claim_type": target["claimType"],
        "notes": target.get("notes"),
        "country": target.get("country"),
        "currency": target.get("currency"),
        "fiscal_period_end": _source_date(target.get("fiscalPeriodEnd")),
        "accounting_standard": target.get("accountingStandard"),
        "market_cap": target.get("marketCap"),
        "revenue_growth_pct": target.get("revenueGrowthPct"),
        "ebitda_margin_pct": target.get("ebitdaMarginPct"),
    }


def _target_from_record(
    record: PeerValuationTargetProfile | PeerValuationRevisionTargetProfile,
) -> dict[str, Any]:
    target = {
        "sourceName": record.source_name,
        "sourceUrl": record.source_url,
        "sourceAsOf": record.source_as_of.isoformat(),
        "claimType": record.claim_type,
        "notes": record.notes,
        "country": record.country,
        "currency": record.currency,
        "fiscalPeriodEnd": (
            record.fiscal_period_end.isoformat() if record.fiscal_period_end else None
        ),
        "accountingStandard": record.accounting_standard,
        "marketCap": record.market_cap,
        "revenueGrowthPct": record.revenue_growth_pct,
        "ebitdaMarginPct": record.ebitda_margin_pct,
    }
    return {key: value for key, value in target.items() if value is not None}


def _record_kwargs(member: dict[str, Any], *, ordinal: int) -> dict[str, Any]:
    multiples = member.get("multiples") or {}
    return {
        "ordinal": ordinal,
        "identifier": member["identifier"],
        "peer_company_id": member.get("companyId"),
        "name": member.get("name"),
        "included": member.get("included", True),
        **{method: multiples.get(method) for method in PEER_MULTIPLE_METHODS},
        "source_name": member.get("sourceName"),
        "source_url": member.get("sourceUrl"),
        "source_as_of": _source_date(member.get("sourceAsOf")),
        "claim_type": member.get("claimType"),
        "notes": member.get("notes"),
        "country": member.get("country"),
        "currency": member.get("currency"),
        "fiscal_period_end": _source_date(member.get("fiscalPeriodEnd")),
        "accounting_standard": member.get("accountingStandard"),
        "market_cap": member.get("marketCap"),
        "revenue_growth_pct": member.get("revenueGrowthPct"),
        "ebitda_margin_pct": member.get("ebitdaMarginPct"),
    }


def _member_from_record(
    record: PeerValuationMemberRecord | PeerValuationRevisionMemberRecord,
) -> dict[str, Any]:
    member: dict[str, Any] = {
        "identifier": record.identifier,
        "companyId": record.peer_company_id,
        "name": record.name,
        "included": record.included,
        "multiples": {
            method: getattr(record, method)
            for method in PEER_MULTIPLE_METHODS
            if getattr(record, method) is not None
        },
        "sourceName": record.source_name,
        "sourceUrl": record.source_url,
        "sourceAsOf": record.source_as_of.isoformat() if record.source_as_of else None,
        "claimType": record.claim_type,
        "notes": record.notes,
        "country": record.country,
        "currency": record.currency,
        "fiscalPeriodEnd": (
            record.fiscal_period_end.isoformat() if record.fiscal_period_end else None
        ),
        "accountingStandard": record.accounting_standard,
        "marketCap": record.market_cap,
        "revenueGrowthPct": record.revenue_growth_pct,
        "ebitdaMarginPct": record.ebitda_margin_pct,
    }
    return {key: value for key, value in member.items() if value is not None}


def _sync_current_member_records(
    db: Session,
    peer_set: PeerValuationSet,
    members: list[dict[str, Any]],
) -> None:
    for record in list(peer_set.member_records):
        db.delete(record)
    peer_set.member_records = []
    db.flush()
    peer_set.member_records = [
        PeerValuationMemberRecord(**_record_kwargs(member, ordinal=ordinal))
        for ordinal, member in enumerate(members)
    ]


def _sync_revision_member_records(
    revision: PeerValuationSetRevision,
    members: list[dict[str, Any]],
) -> None:
    revision.member_records = [
        PeerValuationRevisionMemberRecord(**_record_kwargs(member, ordinal=ordinal))
        for ordinal, member in enumerate(members)
    ]


def _sync_current_target_profile(
    db: Session,
    peer_set: PeerValuationSet,
    target: dict[str, Any],
) -> None:
    if peer_set.target_profile is not None:
        db.delete(peer_set.target_profile)
        peer_set.target_profile = None
        db.flush()
    if target:
        peer_set.target_profile = PeerValuationTargetProfile(**_target_record_kwargs(target))


def _sync_revision_target_profile(
    revision: PeerValuationSetRevision,
    target: dict[str, Any],
) -> None:
    if target:
        revision.target_profile = PeerValuationRevisionTargetProfile(
            **_target_record_kwargs(target)
        )


def _storage_consistency(
    json_members: list[dict[str, Any]],
    normalized_members: list[dict[str, Any]],
) -> dict[str, Any]:
    def canonical(member: dict[str, Any]) -> dict[str, Any]:
        compact = {key: value for key, value in member.items() if value is not None}
        compact["included"] = compact.get("included", True)
        compact["multiples"] = {
            key: value
            for key, value in (compact.get("multiples") or {}).items()
            if value is not None
        }
        return compact

    canonical_json = [canonical(member) for member in json_members]
    canonical_normalized = [canonical(member) for member in normalized_members]
    if not normalized_members and json_members:
        return {
            "status": "legacy_json_only",
            "jsonMemberCount": len(json_members),
            "normalizedMemberCount": 0,
        }
    return {
        "status": "consistent" if canonical_normalized == canonical_json else "mismatch",
        "jsonMemberCount": len(json_members),
        "normalizedMemberCount": len(normalized_members),
    }


def peer_set_members(peer_set: PeerValuationSet) -> list[dict[str, Any]]:
    normalized_members = [_member_from_record(record) for record in peer_set.member_records]
    return normalized_members or (peer_set.peer_identifiers_json or [])


def peer_set_storage_consistency(peer_set: PeerValuationSet) -> dict[str, Any]:
    return _storage_consistency(
        peer_set.peer_identifiers_json or [],
        [_member_from_record(record) for record in peer_set.member_records],
    )


def _target_storage_consistency(
    json_target: dict[str, Any],
    normalized_target: dict[str, Any],
) -> dict[str, Any]:
    if json_target and not normalized_target:
        status = "legacy_json_only"
    elif json_target == normalized_target:
        status = "consistent"
    else:
        status = "mismatch"
    return {
        "status": status,
        "jsonTargetPresent": bool(json_target),
        "normalizedTargetPresent": bool(normalized_target),
    }


def peer_set_target_context(peer_set: PeerValuationSet) -> dict[str, Any] | None:
    normalized = _target_from_record(peer_set.target_profile) if peer_set.target_profile else {}
    return normalized or (peer_set.target_context_json or {}) or None


def peer_set_target_storage_consistency(peer_set: PeerValuationSet) -> dict[str, Any]:
    normalized = _target_from_record(peer_set.target_profile) if peer_set.target_profile else {}
    return _target_storage_consistency(peer_set.target_context_json or {}, normalized)


def _validate_members(
    db: Session,
    *,
    target_company_id: int,
    members: list[PeerMemberInput],
) -> None:
    identifiers: set[str] = set()
    for member in members:
        if member.identifier in identifiers:
            raise HTTPException(
                status_code=422,
                detail=f"Duplicate peer identifier: {member.identifier}",
            )
        identifiers.add(member.identifier)
        if member.companyId is None:
            continue
        if member.companyId == target_company_id:
            raise HTTPException(status_code=422, detail="Target company cannot be its own peer")
        if db.get(Company, member.companyId) is None:
            raise HTTPException(
                status_code=422,
                detail=f"Peer company {member.companyId} was not found",
            )


def calculate_peer_aggregates(members: list[dict[str, Any]]) -> dict[str, Any]:
    method_results: dict[str, Any] = {}
    for method in PEER_MULTIPLE_METHODS:
        eligible: list[tuple[str, float]] = []
        excluded: list[dict[str, str]] = []
        for member in members:
            identifier = str(member.get("identifier") or "unknown")
            if not member.get("included", True):
                excluded.append({"identifier": identifier, "reason": "excluded_by_user"})
                continue
            value = (member.get("multiples") or {}).get(method)
            if value is None:
                excluded.append({"identifier": identifier, "reason": "missing_multiple"})
                continue
            numeric_value = float(value)
            if numeric_value <= 0:
                excluded.append({"identifier": identifier, "reason": "non_positive_multiple"})
                continue
            eligible.append((identifier, numeric_value))
        eligible_count = len(eligible)
        method_results[method] = {
            "multiple": (
                float(median(value for _, value in eligible))
                if eligible_count >= MINIMUM_METHOD_PEERS
                else None
            ),
            "eligibleCount": eligible_count,
            "requiredCount": MINIMUM_METHOD_PEERS,
            "eligibleMemberIdentifiers": [identifier for identifier, _ in eligible],
            "excludedMembers": excluded,
            "formula": "median(positive included peer multiples)",
        }
    return {
        "aggregationMethod": "median",
        "minimumMethodPeers": MINIMUM_METHOD_PEERS,
        "methods": method_results,
    }


def _source_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def _market_cap_context(
    members: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[str], list[str], float | None]:
    groups: dict[str, list[tuple[str, float]]] = {}
    missing_currency: list[str] = []
    invalid_value: list[str] = []
    recorded_count = 0
    for member in members:
        raw_value = member.get("marketCap")
        if raw_value is None:
            continue
        recorded_count += 1
        identifier = str(member.get("identifier") or "unknown")
        try:
            market_cap = float(raw_value)
        except (TypeError, ValueError):
            invalid_value.append(identifier)
            continue
        if not isfinite(market_cap) or market_cap <= 0:
            invalid_value.append(identifier)
            continue
        currency = str(member.get("currency") or "").strip().upper()
        if not currency:
            missing_currency.append(identifier)
            continue
        groups.setdefault(currency, []).append((identifier, market_cap))

    group_diagnostics: dict[str, dict[str, Any]] = {}
    for currency in sorted(groups):
        entries = groups[currency]
        values = [value for _, value in entries]
        group_diagnostics[currency] = {
            "memberCount": len(entries),
            "memberIdentifiers": [identifier for identifier, _ in entries],
            "minimum": min(values),
            "maximum": max(values),
            "maxToMinRatio": max(values) / min(values),
        }

    comparable_ratio = None
    if (
        len(group_diagnostics) == 1
        and not missing_currency
        and not invalid_value
        and recorded_count > 0
    ):
        comparable_ratio = next(iter(group_diagnostics.values()))["maxToMinRatio"]
    return group_diagnostics, missing_currency, invalid_value, comparable_ratio


def calculate_peer_diagnostics(
    members: list[dict[str, Any]],
    *,
    target_context: dict[str, Any] | None = None,
    as_of: date | None = None,
) -> dict[str, Any]:
    evaluation_date = as_of or date.today()
    included = [member for member in members if member.get("included", True)]
    dated_members = [
        (str(member.get("identifier") or "unknown"), parsed)
        for member in included
        if (parsed := _source_date(member.get("sourceAsOf"))) is not None
    ]
    source_dates = [parsed for _, parsed in dated_members]
    earliest = min(source_dates) if source_dates else None
    latest = max(source_dates) if source_dates else None
    span_days = (latest - earliest).days if earliest and latest else None
    stale_identifiers = [
        identifier
        for identifier, source_as_of in dated_members
        if (evaluation_date - source_as_of).days > PEER_SOURCE_STALE_DAYS
    ]
    claim_type_counts = {
        claim_type: sum(1 for member in included if member.get("claimType") == claim_type)
        for claim_type in ("Fact", "Source Summary")
    }
    currencies = sorted({str(member["currency"]) for member in included if member.get("currency")})
    countries = sorted({str(member["country"]) for member in included if member.get("country")})
    accounting_standards = sorted(
        {str(member["accountingStandard"]) for member in included if member.get("accountingStandard")}
    )
    fiscal_dates = [
        parsed
        for member in included
        if (parsed := _source_date(member.get("fiscalPeriodEnd"))) is not None
    ]
    fiscal_span_days = (max(fiscal_dates) - min(fiscal_dates)).days if fiscal_dates else None
    market_cap_count = sum(1 for member in included if member.get("marketCap") is not None)
    (
        market_cap_groups,
        missing_market_cap_currency,
        invalid_market_cap_values,
        market_cap_ratio,
    ) = _market_cap_context(included)
    revenue_growth = [
        float(member["revenueGrowthPct"])
        for member in included
        if member.get("revenueGrowthPct") is not None
    ]
    ebitda_margins = [
        float(member["ebitdaMarginPct"])
        for member in included
        if member.get("ebitdaMarginPct") is not None
    ]

    warnings: list[dict[str, Any]] = []
    target = target_context or {}
    if not target:
        warnings.append(
            {
                "code": "missing_target_context",
                "severity": "warning",
                "message": "No sourced target-company comparability profile is stored.",
                "memberIdentifiers": [],
            }
        )
    else:
        target_source_as_of = _source_date(target.get("sourceAsOf"))
        if (
            target_source_as_of is not None
            and (evaluation_date - target_source_as_of).days > PEER_SOURCE_STALE_DAYS
        ):
            warnings.append(
                {
                    "code": "stale_target_source",
                    "severity": "warning",
                    "message": (
                        "Target-company source is older than "
                        f"{PEER_SOURCE_STALE_DAYS} days."
                    ),
                    "memberIdentifiers": [],
                }
            )
        if target.get("claimType") == "Source Summary":
            warnings.append(
                {
                    "code": "target_source_summary",
                    "severity": "warning",
                    "message": "Target-company context is a Source Summary, not a stored primary-source fact.",
                    "memberIdentifiers": [],
                }
            )
    if stale_identifiers:
        warnings.append(
            {
                "code": "stale_peer_sources",
                "severity": "warning",
                "message": (
                    f"{len(stale_identifiers)} included peer source(s) are older than "
                    f"{PEER_SOURCE_STALE_DAYS} days."
                ),
                "memberIdentifiers": stale_identifiers,
            }
        )
    if span_days is not None and span_days > PEER_SOURCE_DATE_SPAN_WARNING_DAYS:
        warnings.append(
            {
                "code": "unaligned_source_dates",
                "severity": "warning",
                "message": (
                    f"Included peer source dates span {span_days} days; review period alignment."
                ),
                "memberIdentifiers": [identifier for identifier, _ in dated_members],
            }
        )
    if claim_type_counts["Source Summary"]:
        warnings.append(
            {
                "code": "source_summary_members",
                "severity": "warning",
                "message": (
                    f"{claim_type_counts['Source Summary']} included peer(s) are Source Summaries, "
                    "not stored primary-source facts."
                ),
                "memberIdentifiers": [
                    str(member.get("identifier") or "unknown")
                    for member in included
                    if member.get("claimType") == "Source Summary"
                ],
            }
        )
    context_checks = (
        ("currency", len([member for member in included if member.get("currency")])),
        ("country", len([member for member in included if member.get("country")])),
        ("fiscalPeriodEnd", len(fiscal_dates)),
        (
            "accountingStandard",
            len([member for member in included if member.get("accountingStandard")]),
        ),
        ("marketCap", market_cap_count),
        ("revenueGrowthPct", len(revenue_growth)),
        ("ebitdaMarginPct", len(ebitda_margins)),
    )
    partial_fields = [field for field, count in context_checks if 0 < count < len(included)]
    if partial_fields:
        warnings.append(
            {
                "code": "partial_comparability_context",
                "severity": "warning",
                "message": (
                    "Comparability context is only partially populated for: "
                    + ", ".join(partial_fields)
                    + "."
                ),
                "memberIdentifiers": [str(member.get("identifier") or "unknown") for member in included],
            }
        )
    if len(currencies) > 1:
        warnings.append(
            {
                "code": "mixed_peer_currencies",
                "severity": "warning",
                "message": f"Peer evidence mixes currencies: {', '.join(currencies)}.",
                "memberIdentifiers": [str(member.get("identifier") or "unknown") for member in included],
            }
        )
    if missing_market_cap_currency:
        warnings.append(
            {
                "code": "market_cap_currency_missing",
                "severity": "warning",
                "message": (
                    f"{len(missing_market_cap_currency)} peer market cap(s) have no stated "
                    "currency and are excluded from size comparisons."
                ),
                "memberIdentifiers": missing_market_cap_currency,
            }
        )
    if invalid_market_cap_values:
        warnings.append(
            {
                "code": "invalid_market_cap_context",
                "severity": "warning",
                "message": (
                    f"{len(invalid_market_cap_values)} peer market cap value(s) are not positive "
                    "finite amounts and are excluded from size comparisons."
                ),
                "memberIdentifiers": invalid_market_cap_values,
            }
        )
    if len(accounting_standards) > 1:
        warnings.append(
            {
                "code": "mixed_accounting_standards",
                "severity": "warning",
                "message": (
                    "Peer evidence mixes accounting standards: "
                    + ", ".join(accounting_standards)
                    + "."
                ),
                "memberIdentifiers": [str(member.get("identifier") or "unknown") for member in included],
            }
        )
    if fiscal_span_days is not None and fiscal_span_days > PEER_FISCAL_PERIOD_SPAN_WARNING_DAYS:
        warnings.append(
            {
                "code": "unaligned_fiscal_periods",
                "severity": "warning",
                "message": f"Peer fiscal period ends span {fiscal_span_days} days.",
                "memberIdentifiers": [str(member.get("identifier") or "unknown") for member in included],
            }
        )
    for currency, group in market_cap_groups.items():
        if (
            group["memberCount"] >= 2
            and group["maxToMinRatio"] >= PEER_MARKET_CAP_RATIO_WARNING
        ):
            warnings.append(
                {
                    "code": "wide_size_dispersion",
                    "severity": "warning",
                    "currency": currency,
                    "message": (
                        f"Largest {currency} peer market cap is "
                        f"{group['maxToMinRatio']:.1f}x the smallest; review size comparability."
                    ),
                    "memberIdentifiers": group["memberIdentifiers"],
                }
            )
    revenue_growth_span = max(revenue_growth) - min(revenue_growth) if revenue_growth else None
    if revenue_growth_span is not None and revenue_growth_span >= PEER_GROWTH_SPAN_WARNING_PCT:
        warnings.append(
            {
                "code": "wide_growth_dispersion",
                "severity": "warning",
                "message": f"Peer revenue growth spans {revenue_growth_span:.1f} percentage points.",
                "memberIdentifiers": [str(member.get("identifier") or "unknown") for member in included],
            }
        )
    margin_span = max(ebitda_margins) - min(ebitda_margins) if ebitda_margins else None
    if margin_span is not None and margin_span >= PEER_MARGIN_SPAN_WARNING_PCT:
        warnings.append(
            {
                "code": "wide_margin_dispersion",
                "severity": "warning",
                "message": f"Peer EBITDA margins span {margin_span:.1f} percentage points.",
                "memberIdentifiers": [str(member.get("identifier") or "unknown") for member in included],
            }
        )

    target_comparisons: dict[str, Any] = {}
    for field, code, label in (
        ("currency", "target_currency_mismatch", "currency"),
        ("country", "target_country_mismatch", "country"),
        ("accountingStandard", "target_accounting_mismatch", "accounting standard"),
    ):
        target_value = target.get(field)
        if not target_value:
            continue
        mismatched = [
            str(member.get("identifier") or "unknown")
            for member in included
            if member.get(field) and member.get(field) != target_value
        ]
        compared = sum(1 for member in included if member.get(field))
        target_comparisons[field] = {"comparedCount": compared, "mismatchCount": len(mismatched)}
        if mismatched:
            warnings.append(
                {
                    "code": code,
                    "severity": "warning",
                    "message": (
                        f"{len(mismatched)} peer(s) use a different {label} than "
                        f"the target ({target_value})."
                    ),
                    "memberIdentifiers": mismatched,
                }
            )

    target_fiscal_date = _source_date(target.get("fiscalPeriodEnd"))
    if target_fiscal_date is not None:
        fiscal_mismatches = [
            str(member.get("identifier") or "unknown")
            for member in included
            if (peer_date := _source_date(member.get("fiscalPeriodEnd"))) is not None
            and abs((peer_date - target_fiscal_date).days)
            > PEER_FISCAL_PERIOD_SPAN_WARNING_DAYS
        ]
        target_comparisons["fiscalPeriodEnd"] = {
            "comparedCount": len(fiscal_dates),
            "mismatchCount": len(fiscal_mismatches),
        }
        if fiscal_mismatches:
            warnings.append(
                {
                    "code": "target_fiscal_period_mismatch",
                    "severity": "warning",
                    "message": (
                        f"{len(fiscal_mismatches)} peer fiscal period(s) differ from the target "
                        f"by more than {PEER_FISCAL_PERIOD_SPAN_WARNING_DAYS} days."
                    ),
                    "memberIdentifiers": fiscal_mismatches,
                }
            )

    target_market_cap = target.get("marketCap")
    if target_market_cap is not None:
        target_currency = str(target.get("currency") or "").strip().upper() or None
        compared: dict[str, float] = {}
        mismatched: list[str] = []
        skipped_currency: list[str] = []
        skipped_missing_currency: list[str] = []
        skipped_invalid: list[str] = []
        try:
            numeric_target_market_cap = float(target_market_cap)
        except (TypeError, ValueError):
            numeric_target_market_cap = 0.0
        target_is_valid = isfinite(numeric_target_market_cap) and numeric_target_market_cap > 0
        positive_peer_ids: list[str] = []
        for member in included:
            peer_value = member.get("marketCap")
            if peer_value is None:
                continue
            identifier = str(member.get("identifier") or "unknown")
            try:
                numeric_peer_value = float(peer_value)
            except (TypeError, ValueError):
                skipped_invalid.append(identifier)
                continue
            if not isfinite(numeric_peer_value) or numeric_peer_value <= 0:
                skipped_invalid.append(identifier)
                continue
            positive_peer_ids.append(identifier)
            peer_currency = str(member.get("currency") or "").strip().upper() or None
            if not target_currency:
                skipped_missing_currency.append(identifier)
                continue
            if not peer_currency:
                skipped_missing_currency.append(identifier)
                continue
            if peer_currency != target_currency:
                skipped_currency.append(identifier)
                continue
            if not target_is_valid:
                continue
            delta = max(numeric_target_market_cap, numeric_peer_value) / min(
                numeric_target_market_cap, numeric_peer_value
            )
            compared[identifier] = delta
            if delta >= PEER_MARKET_CAP_RATIO_WARNING:
                mismatched.append(identifier)

        skipped_ids = [
            identifier
            for identifier in positive_peer_ids + skipped_invalid
            if identifier in {*skipped_currency, *skipped_missing_currency, *skipped_invalid}
        ]
        target_comparisons["marketCap"] = {
            "comparedCount": len(compared),
            "mismatchCount": len(mismatched),
            "maximumDifference": max(compared.values()) if compared else None,
            "currency": target_currency,
            "skippedCurrencyMismatchCount": len(skipped_currency),
            "skippedMissingCurrencyCount": len(skipped_missing_currency),
            "skippedInvalidValueCount": len(skipped_invalid),
            "skippedMemberIdentifiers": skipped_ids,
        }
        if not target_is_valid:
            warnings.append(
                {
                    "code": "invalid_target_market_cap_context",
                    "severity": "warning",
                    "message": "Target market cap is not a positive finite amount; size comparison is unavailable.",
                    "memberIdentifiers": [],
                }
            )
        elif not target_currency:
            warnings.append(
                {
                    "code": "target_size_currency_missing",
                    "severity": "warning",
                    "message": (
                        "Target market cap has no stated currency, so target-size comparison is unavailable."
                    ),
                    "memberIdentifiers": positive_peer_ids,
                }
            )
        else:
            if skipped_ids:
                warnings.append(
                    {
                        "code": "target_size_comparison_limited",
                        "severity": "warning",
                        "message": (
                            f"Target market-cap comparison skipped {len(skipped_ids)} peer(s) "
                            "with a different, missing, or unusable currency/value."
                        ),
                        "memberIdentifiers": skipped_ids,
                    }
                )
            if mismatched:
                warnings.append(
                    {
                        "code": "target_size_mismatch",
                        "severity": "warning",
                        "currency": target_currency,
                        "message": (
                            f"{len(mismatched)} same-currency peer(s) differ materially from "
                            f"target market cap; threshold is {PEER_MARKET_CAP_RATIO_WARNING:g}x."
                        ),
                        "memberIdentifiers": mismatched,
                    }
                )

    for field, threshold, code, label in (
        ("revenueGrowthPct", PEER_GROWTH_SPAN_WARNING_PCT, "target_growth_mismatch", "revenue growth"),
        ("ebitdaMarginPct", PEER_MARGIN_SPAN_WARNING_PCT, "target_margin_mismatch", "EBITDA margin"),
    ):
        target_value = target.get(field)
        if target_value is None:
            continue
        mismatched: list[str] = []
        deltas: dict[str, float] = {}
        for member in included:
            peer_value = member.get(field)
            if peer_value is None:
                continue
            identifier = str(member.get("identifier") or "unknown")
            delta = abs(float(peer_value) - float(target_value))
            deltas[identifier] = delta
            if delta >= threshold:
                mismatched.append(identifier)
        target_comparisons[field] = {
            "comparedCount": len(deltas),
            "mismatchCount": len(mismatched),
            "maximumDifference": max(deltas.values()) if deltas else None,
        }
        if mismatched:
            warnings.append(
                {
                    "code": code,
                    "severity": "warning",
                    "message": (
                        f"{len(mismatched)} peer(s) differ materially from target {label}; "
                        f"threshold is {threshold:g} percentage points."
                    ),
                    "memberIdentifiers": mismatched,
                }
            )

    method_diagnostics: dict[str, Any] = {}
    for method in PEER_MULTIPLE_METHODS:
        eligible = [
            (str(member.get("identifier") or "unknown"), float(value))
            for member in included
            if (value := (member.get("multiples") or {}).get(method)) is not None
            and float(value) > 0
        ]
        values = [value for _, value in eligible]
        method_median = float(median(values)) if values else None
        method_mad = (
            float(median(abs(value - method_median) for value in values))
            if method_median is not None
            else None
        )
        ratio = max(values) / min(values) if values else None
        relative_mad = (
            method_mad / method_median
            if method_mad is not None and method_median and method_median > 0
            else None
        )
        method_warnings: list[str] = []
        if 0 < len(values) < MINIMUM_METHOD_PEERS:
            method_warnings.append("insufficient_coverage")
            warnings.append(
                {
                    "code": "insufficient_method_coverage",
                    "severity": "warning",
                    "method": method,
                    "message": (
                        f"{method.upper()} has {len(values)} eligible peer value(s); "
                        f"{MINIMUM_METHOD_PEERS} are required."
                    ),
                    "memberIdentifiers": [identifier for identifier, _ in eligible],
                }
            )
        if len(values) >= MINIMUM_METHOD_PEERS and (
            (ratio is not None and ratio >= PEER_MULTIPLE_RATIO_WARNING)
            or (relative_mad is not None and relative_mad >= PEER_RELATIVE_MAD_WARNING)
        ):
            method_warnings.append("wide_dispersion")
            warnings.append(
                {
                    "code": "wide_multiple_dispersion",
                    "severity": "warning",
                    "method": method,
                    "message": (
                        f"{method.upper()} peer values are widely dispersed; "
                        "the median does not resolve comparability differences."
                    ),
                    "memberIdentifiers": [identifier for identifier, _ in eligible],
                }
            )
        method_diagnostics[method] = {
            "eligibleCount": len(values),
            "minimum": min(values) if values else None,
            "maximum": max(values) if values else None,
            "median": method_median,
            "medianAbsoluteDeviation": method_mad,
            "relativeMedianAbsoluteDeviation": relative_mad,
            "maxToMinRatio": ratio,
            "warnings": method_warnings,
        }

    diagnostics = {
        "status": "review_required" if warnings else "bounded",
        "asOf": evaluation_date.isoformat(),
        "thresholds": {
            "sourceStaleDays": PEER_SOURCE_STALE_DAYS,
            "sourceDateSpanWarningDays": PEER_SOURCE_DATE_SPAN_WARNING_DAYS,
            "multipleRatioWarning": PEER_MULTIPLE_RATIO_WARNING,
            "relativeMedianAbsoluteDeviationWarning": PEER_RELATIVE_MAD_WARNING,
            "fiscalPeriodSpanWarningDays": PEER_FISCAL_PERIOD_SPAN_WARNING_DAYS,
            "marketCapRatioWarning": PEER_MARKET_CAP_RATIO_WARNING,
            "growthSpanWarningPct": PEER_GROWTH_SPAN_WARNING_PCT,
            "marginSpanWarningPct": PEER_MARGIN_SPAN_WARNING_PCT,
        },
        "sourceDates": {
            "earliest": earliest.isoformat() if earliest else None,
            "latest": latest.isoformat() if latest else None,
            "spanDays": span_days,
            "staleMemberIdentifiers": stale_identifiers,
        },
        "claimTypeCounts": claim_type_counts,
        "comparabilityContext": {
            "countries": countries,
            "currencies": currencies,
            "accountingStandards": accounting_standards,
            "fiscalPeriodSpanDays": fiscal_span_days,
            "marketCapRatio": market_cap_ratio,
            "marketCapGroups": market_cap_groups,
            "unusableMarketCapMemberIdentifiers": missing_market_cap_currency,
            "invalidMarketCapMemberIdentifiers": invalid_market_cap_values,
            "revenueGrowthSpanPct": revenue_growth_span,
            "ebitdaMarginSpanPct": margin_span,
            "coverage": {field: count for field, count in context_checks},
            "targetProvided": bool(target),
            "targetComparisons": target_comparisons,
        },
        "methods": method_diagnostics,
        "warnings": warnings,
    }
    diagnostics["warningCodes"] = sorted({str(item["code"]) for item in warnings})
    canonical = json.dumps(
        diagnostics,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    diagnostics["acknowledgementSha256"] = sha256(canonical).hexdigest()
    return diagnostics


def peer_review_receipt(
    *,
    diagnostics_sha256: str | None,
    warning_codes: list[str] | None,
    diagnostics_as_of: date | None,
    current_diagnostics: dict[str, Any],
) -> dict[str, Any] | None:
    if not diagnostics_sha256 or diagnostics_as_of is None:
        return None
    return {
        "diagnosticsSha256": diagnostics_sha256,
        "warningCodes": warning_codes or [],
        "diagnosticsAsOf": diagnostics_as_of.isoformat(),
        "matchesCurrentDiagnostics": peer_review_receipt_matches(
            diagnostics_sha256=diagnostics_sha256,
            warning_codes=warning_codes,
            diagnostics_as_of=diagnostics_as_of,
            current_diagnostics=current_diagnostics,
        ),
    }


def peer_review_receipt_matches(
    *,
    diagnostics_sha256: str | None,
    warning_codes: list[str] | None,
    diagnostics_as_of: date | None,
    current_diagnostics: dict[str, Any],
) -> bool:
    return bool(
        diagnostics_sha256
        and diagnostics_as_of
        and warning_codes is not None
        and diagnostics_sha256 == current_diagnostics["acknowledgementSha256"]
        and (warning_codes or []) == current_diagnostics["warningCodes"]
        and diagnostics_as_of.isoformat() == current_diagnostics["asOf"]
    )


def peer_set_calculation_eligibility(
    peer_set: PeerValuationSet,
    *,
    diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Peer evidence eligibility only; company financial inputs are checked at run time."""
    members = peer_set_members(peer_set)
    diagnostics = diagnostics or calculate_peer_diagnostics(
        members, target_context=peer_set_target_context(peer_set),
    )
    receipt_missing = (
        not peer_set.review_diagnostics_sha256
        or peer_set.review_warning_codes_json is None
        or peer_set.review_diagnostics_as_of is None
    )
    receipt_status = "missing" if receipt_missing else (
        "current" if peer_review_receipt_matches(
            diagnostics_sha256=peer_set.review_diagnostics_sha256,
            warning_codes=peer_set.review_warning_codes_json,
            diagnostics_as_of=peer_set.review_diagnostics_as_of,
            current_diagnostics=diagnostics,
        ) else "stale"
    )
    blockers: list[str] = []
    if not peer_set.is_active:
        blockers.append("archived")
    if peer_set.review_status != "reviewed":
        blockers.append("review_required")
    if peer_set_storage_consistency(peer_set)["status"] == "mismatch":
        blockers.append("member_storage_mismatch")
    if peer_set_target_storage_consistency(peer_set)["status"] == "mismatch":
        blockers.append("target_storage_mismatch")
    if receipt_status != "current":
        blockers.append(f"receipt_{receipt_status}")
    usable_methods = [
        method for method, result in calculate_peer_aggregates(members)["methods"].items()
        if result["multiple"] is not None
    ]
    if not usable_methods:
        blockers.append("insufficient_method_coverage")
    return {
        "canCalculate": not blockers,
        "receiptStatus": receipt_status,
        "usableMethods": usable_methods,
        "blockers": blockers,
        "asOf": diagnostics["asOf"],
    }


def _owned_set(db: Session, peer_set_id: int, user_id: str) -> PeerValuationSet:
    peer_set = db.scalar(
        select(PeerValuationSet).where(
            PeerValuationSet.id == peer_set_id,
            PeerValuationSet.user_id == user_id,
        )
    )
    if peer_set is None:
        raise HTTPException(status_code=404, detail="Peer valuation set not found")
    return peer_set


def _require_version(peer_set: PeerValuationSet, expected_version: int) -> None:
    if peer_set.version != expected_version:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Peer valuation set changed from version {expected_version} "
                f"to {peer_set.version}; reload before saving."
            ),
        )


def _record_revision(
    db: Session,
    *,
    peer_set: PeerValuationSet,
    action: str,
    changed_fields: list[str],
) -> PeerValuationSetRevision:
    revision = PeerValuationSetRevision(
        peer_set_id=peer_set.id,
        user_id=peer_set.user_id,
        version=peer_set.version,
        action=action,
        changed_fields_json=changed_fields,
        name=peer_set.name,
        notes=peer_set.notes,
        is_active=peer_set.is_active,
        review_status=peer_set.review_status,
        reviewed_at=peer_set.reviewed_at,
        reviewed_by_user_id=peer_set.reviewed_by_user_id,
        review_diagnostics_sha256=peer_set.review_diagnostics_sha256,
        review_warning_codes_json=peer_set.review_warning_codes_json,
        review_diagnostics_as_of=peer_set.review_diagnostics_as_of,
        aggregation_method=peer_set.aggregation_method,
        members_json=peer_set.peer_identifiers_json or [],
        target_context_json=peer_set.target_context_json or {},
        aggregate_metrics_json=peer_set.aggregate_metrics_json or {},
    )
    db.add(revision)
    db.flush()
    _sync_revision_member_records(revision, peer_set.peer_identifiers_json or [])
    _sync_revision_target_profile(revision, peer_set.target_context_json or {})
    return revision


def peer_set_revision_response(revision: PeerValuationSetRevision) -> dict[str, Any]:
    json_members = revision.members_json or []
    normalized_members = [_member_from_record(record) for record in revision.member_records]
    members = normalized_members or json_members
    json_target = revision.target_context_json or {}
    normalized_target = (
        _target_from_record(revision.target_profile) if revision.target_profile else {}
    )
    target = normalized_target or json_target or None
    diagnostics = calculate_peer_diagnostics(
        members,
        target_context=target,
        as_of=revision.review_diagnostics_as_of,
    )
    return {
        "id": revision.id,
        "peerSetId": revision.peer_set_id,
        "version": revision.version,
        "action": revision.action,
        "changedFields": revision.changed_fields_json or [],
        "name": revision.name,
        "notes": revision.notes,
        "isActive": revision.is_active,
        "reviewStatus": revision.review_status,
        "reviewedAt": revision.reviewed_at,
        "aggregationMethod": revision.aggregation_method,
        "memberCount": len(members),
        "includedMemberCount": sum(1 for member in members if member.get("included", True)),
        "members": members,
        "targetContext": target,
        "aggregates": revision.aggregate_metrics_json or calculate_peer_aggregates(members),
        "diagnostics": diagnostics,
        "reviewReceipt": peer_review_receipt(
            diagnostics_sha256=revision.review_diagnostics_sha256,
            warning_codes=revision.review_warning_codes_json,
            diagnostics_as_of=revision.review_diagnostics_as_of,
            current_diagnostics=diagnostics,
        ),
        "storageConsistency": _storage_consistency(json_members, normalized_members),
        "targetStorageConsistency": _target_storage_consistency(
            json_target, normalized_target
        ),
        "createdAt": revision.created_at,
    }


def _member_sources(peer_set: PeerValuationSet, identifiers: list[str]) -> list[dict[str, Any]]:
    wanted = set(identifiers)
    return [
        {
            "identifier": member["identifier"],
            "companyId": member.get("companyId"),
            "name": member.get("name"),
            "sourceName": member["sourceName"],
            "sourceUrl": member["sourceUrl"],
            "sourceAsOf": member["sourceAsOf"],
            "claimType": member["claimType"],
        }
        for member in peer_set_members(peer_set)
        if member.get("identifier") in wanted
    ]


def peer_set_response(peer_set: PeerValuationSet, *, include_members: bool = True) -> dict[str, Any]:
    json_members = peer_set.peer_identifiers_json or []
    normalized_members = [_member_from_record(record) for record in peer_set.member_records]
    members = normalized_members or json_members
    target = peer_set_target_context(peer_set)
    diagnostics = calculate_peer_diagnostics(members, target_context=target)
    response = {
        "id": peer_set.id,
        "companyId": peer_set.company_id,
        "name": peer_set.name,
        "notes": peer_set.notes,
        "isActive": peer_set.is_active,
        "reviewStatus": peer_set.review_status,
        "reviewedAt": peer_set.reviewed_at,
        "aggregationMethod": peer_set.aggregation_method,
        "version": peer_set.version,
        "aggregates": calculate_peer_aggregates(members),
        "diagnostics": diagnostics,
        "calculationEligibility": peer_set_calculation_eligibility(peer_set, diagnostics=diagnostics),
        "reviewReceipt": peer_review_receipt(
            diagnostics_sha256=peer_set.review_diagnostics_sha256,
            warning_codes=peer_set.review_warning_codes_json,
            diagnostics_as_of=peer_set.review_diagnostics_as_of,
            current_diagnostics=diagnostics,
        ),
        "storageConsistency": _storage_consistency(json_members, normalized_members),
        "targetStorageConsistency": peer_set_target_storage_consistency(peer_set),
        "targetContext": target,
        "importSha256": peer_set.import_sha256,
        "memberCount": len(members),
        "includedMemberCount": sum(1 for member in members if member.get("included", True)),
        "createdAt": peer_set.created_at,
        "updatedAt": peer_set.updated_at,
    }
    if include_members:
        response["members"] = members
    return response


class PeerValuationSetService:
    @staticmethod
    def list_sets(
        db: Session,
        *,
        user_id: str,
        company_id: int | None = None,
        include_archived: bool = False,
    ) -> list[dict[str, Any]]:
        query = (
            select(PeerValuationSet)
            .options(
                selectinload(PeerValuationSet.member_records),
                selectinload(PeerValuationSet.target_profile),
            )
            .where(PeerValuationSet.user_id == user_id)
        )
        if company_id is not None:
            query = query.where(PeerValuationSet.company_id == company_id)
        if not include_archived:
            query = query.where(PeerValuationSet.is_active.is_(True))
        rows = db.scalars(query.order_by(PeerValuationSet.updated_at.desc(), PeerValuationSet.id.desc()))
        return [peer_set_response(row, include_members=False) for row in rows]

    @staticmethod
    def get_set(db: Session, *, peer_set_id: int, user_id: str) -> PeerValuationSet:
        peer_set = db.scalar(
            select(PeerValuationSet)
            .options(
                selectinload(PeerValuationSet.member_records),
                selectinload(PeerValuationSet.target_profile),
            )
            .where(
                PeerValuationSet.id == peer_set_id,
                PeerValuationSet.user_id == user_id,
            )
        )
        if peer_set is None:
            raise HTTPException(status_code=404, detail="Peer valuation set not found")
        return peer_set

    @staticmethod
    def create_set(
        db: Session,
        *,
        user_id: str,
        payload: PeerValuationSetCreate,
        revision_action: str = "create",
        import_sha256: str | None = None,
    ) -> PeerValuationSet:
        if db.get(Company, payload.companyId) is None:
            raise HTTPException(status_code=404, detail="Target company not found")
        _validate_members(
            db,
            target_company_id=payload.companyId,
            members=payload.members,
        )
        members = [_member_dict(member) for member in payload.members]
        target = _target_dict(payload.targetContext)
        peer_set = PeerValuationSet(
            company_id=payload.companyId,
            user_id=user_id,
            name=payload.name,
            notes=payload.notes,
            peer_identifiers_json=members,
            target_context_json=target,
            import_sha256=import_sha256,
            aggregate_metrics_json=calculate_peer_aggregates(members),
            aggregation_method="median",
            review_status="draft",
            is_active=True,
            version=1,
        )
        _sync_current_member_records(db, peer_set, members)
        _sync_current_target_profile(db, peer_set, target)
        db.add(peer_set)
        db.flush()
        _record_revision(
            db,
            peer_set=peer_set,
            action=revision_action,
            changed_fields=["name", "notes", "members"]
            + (["targetContext"] if target else []),
        )
        db.commit()
        db.refresh(peer_set)
        return peer_set

    @staticmethod
    def update_set(
        db: Session,
        *,
        peer_set_id: int,
        user_id: str,
        payload: PeerValuationSetUpdate,
    ) -> PeerValuationSet:
        peer_set = _owned_set(db, peer_set_id, user_id)
        if not peer_set.is_active:
            raise HTTPException(status_code=409, detail="Archived peer valuation set cannot be edited")
        _require_version(peer_set, payload.expectedVersion)
        changes = payload.model_dump(exclude_unset=True)
        changed_fields: list[str] = []
        if "name" in changes and peer_set.name != changes["name"]:
            peer_set.name = changes["name"]
            changed_fields.append("name")
        if "notes" in changes and peer_set.notes != changes["notes"]:
            peer_set.notes = changes["notes"]
            changed_fields.append("notes")
        if payload.members is not None:
            _validate_members(
                db,
                target_company_id=peer_set.company_id,
                members=payload.members,
            )
            members = [_member_dict(member) for member in payload.members]
            if members != (peer_set.peer_identifiers_json or []):
                peer_set.peer_identifiers_json = members
                peer_set.aggregate_metrics_json = calculate_peer_aggregates(members)
                _sync_current_member_records(db, peer_set, members)
                changed_fields.append("members")
        if "targetContext" in changes:
            target = _target_dict(payload.targetContext)
            if target != (peer_set.target_context_json or {}):
                peer_set.target_context_json = target
                _sync_current_target_profile(db, peer_set, target)
                changed_fields.append("targetContext")
        if not changed_fields:
            raise HTTPException(status_code=409, detail="Peer valuation set update contains no changes")
        had_review = peer_set.review_status == "reviewed"
        had_receipt = bool(peer_set.review_diagnostics_sha256)
        if had_review:
            changed_fields.append("reviewStatus")
        if had_receipt:
            changed_fields.append("reviewReceipt")
        peer_set.review_status = "draft"
        peer_set.reviewed_at = None
        peer_set.reviewed_by_user_id = None
        peer_set.review_diagnostics_sha256 = None
        peer_set.review_warning_codes_json = None
        peer_set.review_diagnostics_as_of = None
        peer_set.version += 1
        _record_revision(
            db,
            peer_set=peer_set,
            action="update",
            changed_fields=changed_fields,
        )
        db.commit()
        db.refresh(peer_set)
        return peer_set

    @staticmethod
    def review_set(
        db: Session,
        *,
        peer_set_id: int,
        user_id: str,
        payload: PeerValuationSetReview,
    ) -> PeerValuationSet:
        peer_set = _owned_set(db, peer_set_id, user_id)
        if not peer_set.is_active:
            raise HTTPException(status_code=409, detail="Archived peer valuation set cannot be reviewed")
        _require_version(peer_set, payload.expectedVersion)
        if not payload.acknowledged:
            raise HTTPException(status_code=422, detail="Peer evidence review must be acknowledged")
        consistency = peer_set_storage_consistency(peer_set)
        if consistency["status"] == "mismatch":
            raise HTTPException(
                status_code=409,
                detail="Peer member storage mismatch must be repaired before review",
            )
        target_consistency = peer_set_target_storage_consistency(peer_set)
        if target_consistency["status"] == "mismatch":
            raise HTTPException(
                status_code=409,
                detail="Target profile storage mismatch must be repaired before review",
            )
        members = peer_set_members(peer_set)
        included_count = sum(1 for member in members if member.get("included", True))
        if included_count < MINIMUM_METHOD_PEERS:
            raise HTTPException(
                status_code=422,
                detail=f"At least {MINIMUM_METHOD_PEERS} included peers are required for review",
            )
        aggregates = calculate_peer_aggregates(members)
        if not any(
            method["multiple"] is not None
            for method in aggregates["methods"].values()
        ):
            raise HTTPException(
                status_code=422,
                detail=f"At least one multiple needs {MINIMUM_METHOD_PEERS} eligible peer values",
            )
        diagnostics = calculate_peer_diagnostics(
            members,
            target_context=peer_set_target_context(peer_set),
        )
        if payload.expectedDiagnosticsSha256 != diagnostics["acknowledgementSha256"]:
            raise HTTPException(
                status_code=409,
                detail="Peer diagnostics changed; reload and review the current warnings.",
            )
        if payload.acknowledgedWarningCodes != diagnostics["warningCodes"]:
            raise HTTPException(
                status_code=422,
                detail="Acknowledged warning codes must exactly match the current diagnostics.",
            )
        if (
            peer_set.review_status == "reviewed"
            and peer_review_receipt_matches(
                diagnostics_sha256=peer_set.review_diagnostics_sha256,
                warning_codes=peer_set.review_warning_codes_json,
                diagnostics_as_of=peer_set.review_diagnostics_as_of,
                current_diagnostics=diagnostics,
            )
        ):
            raise HTTPException(status_code=409, detail="Peer valuation set is already reviewed")
        was_reviewed = peer_set.review_status == "reviewed"
        peer_set.aggregate_metrics_json = aggregates
        peer_set.review_status = "reviewed"
        peer_set.reviewed_at = datetime.now(UTC)
        peer_set.reviewed_by_user_id = user_id
        peer_set.review_diagnostics_sha256 = diagnostics["acknowledgementSha256"]
        peer_set.review_warning_codes_json = diagnostics["warningCodes"]
        peer_set.review_diagnostics_as_of = date.fromisoformat(diagnostics["asOf"])
        peer_set.version += 1
        _record_revision(
            db,
            peer_set=peer_set,
            action="review",
            changed_fields=([] if was_reviewed else ["reviewStatus"])
            + ["reviewedAt", "reviewedByUserId", "reviewReceipt"],
        )
        db.commit()
        db.refresh(peer_set)
        return peer_set

    @staticmethod
    def archive_set(
        db: Session,
        *,
        peer_set_id: int,
        user_id: str,
        expected_version: int,
    ) -> PeerValuationSet:
        peer_set = _owned_set(db, peer_set_id, user_id)
        _require_version(peer_set, expected_version)
        if not peer_set.is_active:
            raise HTTPException(status_code=409, detail="Peer valuation set is already archived")
        peer_set.is_active = False
        peer_set.version += 1
        _record_revision(
            db,
            peer_set=peer_set,
            action="archive",
            changed_fields=["isActive"],
        )
        db.commit()
        db.refresh(peer_set)
        return peer_set

    @staticmethod
    def restore_set(
        db: Session,
        *,
        peer_set_id: int,
        user_id: str,
        payload: PeerValuationSetMutation,
    ) -> PeerValuationSet:
        peer_set = _owned_set(db, peer_set_id, user_id)
        _require_version(peer_set, payload.expectedVersion)
        if peer_set.is_active:
            raise HTTPException(status_code=409, detail="Peer valuation set is already active")
        changed_fields = ["isActive"]
        peer_set.is_active = True
        if peer_set.review_status != "draft":
            changed_fields.extend(["reviewStatus", "reviewedAt", "reviewedByUserId"])
        if peer_set.review_diagnostics_sha256:
            changed_fields.append("reviewReceipt")
        peer_set.review_status = "draft"
        peer_set.reviewed_at = None
        peer_set.reviewed_by_user_id = None
        peer_set.review_diagnostics_sha256 = None
        peer_set.review_warning_codes_json = None
        peer_set.review_diagnostics_as_of = None
        peer_set.version += 1
        _record_revision(
            db,
            peer_set=peer_set,
            action="restore",
            changed_fields=changed_fields,
        )
        db.commit()
        db.refresh(peer_set)
        return peer_set

    @staticmethod
    def list_revisions(
        db: Session,
        *,
        peer_set_id: int,
        user_id: str,
    ) -> list[dict[str, Any]]:
        _owned_set(db, peer_set_id, user_id)
        revisions = db.scalars(
            select(PeerValuationSetRevision)
            .options(
                selectinload(PeerValuationSetRevision.member_records),
                selectinload(PeerValuationSetRevision.target_profile),
            )
            .where(
                PeerValuationSetRevision.peer_set_id == peer_set_id,
                PeerValuationSetRevision.user_id == user_id,
            )
            .order_by(PeerValuationSetRevision.version.desc())
        )
        return [peer_set_revision_response(revision) for revision in revisions]

    @staticmethod
    def method_source(peer_set: PeerValuationSet, method: str) -> dict[str, Any] | None:
        members = peer_set_members(peer_set)
        method_result = calculate_peer_aggregates(members).get("methods", {}).get(method)
        if not method_result or method_result.get("multiple") is None:
            return None
        identifiers = list(method_result.get("eligibleMemberIdentifiers") or [])
        target = peer_set_target_context(peer_set)
        diagnostics = calculate_peer_diagnostics(members, target_context=target)
        return {
            "peerSetId": peer_set.id,
            "peerSetName": peer_set.name,
            "reviewStatus": peer_set.review_status,
            "reviewedAt": peer_set.reviewed_at,
            "aggregationMethod": peer_set.aggregation_method,
            "eligibleCount": method_result["eligibleCount"],
            "eligibleMemberIdentifiers": identifiers,
            "memberSources": _member_sources(peer_set, identifiers),
            "targetContext": target,
            "formula": method_result["formula"],
            "diagnostics": diagnostics["methods"][method],
            "warnings": [
                warning
                for warning in diagnostics["warnings"]
                if warning.get("method") in (None, method)
            ],
            "claimType": "Calculation",
        }
