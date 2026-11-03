from __future__ import annotations
from datetime import date
from hashlib import sha256
import json
from math import isfinite
from statistics import median
from typing import Any
from app.schemas.peer_valuation import PEER_MULTIPLE_METHODS

MINIMUM_METHOD_PEERS = 3


PEER_SOURCE_STALE_DAYS = 120


PEER_SOURCE_DATE_SPAN_WARNING_DAYS = 45


PEER_MULTIPLE_RATIO_WARNING = 3.0


PEER_RELATIVE_MAD_WARNING = 0.5


PEER_FISCAL_PERIOD_SPAN_WARNING_DAYS = 120


PEER_MARKET_CAP_RATIO_WARNING = 10.0


PEER_GROWTH_SPAN_WARNING_PCT = 20.0


PEER_MARGIN_SPAN_WARNING_PCT = 15.0


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
