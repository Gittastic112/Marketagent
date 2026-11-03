from datetime import date

from app.services.peer_valuation_sets import calculate_peer_diagnostics


def _member(
    identifier: str,
    market_cap: float | None,
    currency: str | None,
    *,
    included: bool = True,
) -> dict:
    return {
        "identifier": identifier,
        "included": included,
        "sourceAsOf": date.today().isoformat(),
        "claimType": "Fact",
        "marketCap": market_cap,
        "currency": currency,
        "multiples": {"pe": 12},
    }


def _codes(result: dict) -> set[str]:
    return {warning["code"] for warning in result["warnings"]}


def test_peer_size_dispersion_is_grouped_by_currency() -> None:
    result = calculate_peer_diagnostics(
        [
            _member("USD1", 1_000_000, "USD"),
            _member("EUR1", 20_000_000, "EUR"),
            _member("USD2", 2_000_000, "USD"),
        ]
    )
    context = result["comparabilityContext"]

    assert "wide_size_dispersion" not in _codes(result)
    assert context["marketCapRatio"] is None
    assert context["marketCapGroups"]["USD"]["maxToMinRatio"] == 2.0
    assert context["marketCapGroups"]["USD"]["memberIdentifiers"] == ["USD1", "USD2"]
    assert context["marketCapGroups"]["EUR"]["memberCount"] == 1


def test_same_currency_wide_size_dispersion_remains_visible() -> None:
    result = calculate_peer_diagnostics(
        [
            _member("SMALL", 1_000_000, "USD"),
            _member("LARGE", 12_000_000, "USD"),
            _member("MID", 2_000_000, "USD"),
        ]
    )
    warnings = [warning for warning in result["warnings"] if warning["code"] == "wide_size_dispersion"]

    assert result["comparabilityContext"]["marketCapRatio"] == 12.0
    assert len(warnings) == 1
    assert warnings[0]["currency"] == "USD"
    assert warnings[0]["memberIdentifiers"] == ["SMALL", "LARGE", "MID"]


def test_market_cap_without_currency_is_excluded_and_disclosed() -> None:
    result = calculate_peer_diagnostics(
        [
            _member("UNKNOWN", 50_000_000, None),
            _member("USD1", 1_000_000, "USD"),
            _member("USD2", 2_000_000, "USD"),
        ]
    )
    context = result["comparabilityContext"]

    assert "market_cap_currency_missing" in _codes(result)
    assert context["marketCapRatio"] is None
    assert context["unusableMarketCapMemberIdentifiers"] == ["UNKNOWN"]
    assert context["marketCapGroups"]["USD"]["memberCount"] == 2


def test_target_size_compares_only_matching_currency() -> None:
    result = calculate_peer_diagnostics(
        [
            _member("USD-SAME", 2_000_000, "USD"),
            _member("USD-WIDE", 30_000_000, "USD"),
            _member("EUR", 100_000_000, "EUR"),
            _member("UNKNOWN", 100_000_000, None),
        ],
        target_context={"marketCap": 2_000_000, "currency": "USD"},
    )
    comparison = result["comparabilityContext"]["targetComparisons"]["marketCap"]

    assert comparison == {
        "comparedCount": 2,
        "mismatchCount": 1,
        "maximumDifference": 15.0,
        "currency": "USD",
        "skippedCurrencyMismatchCount": 1,
        "skippedMissingCurrencyCount": 1,
        "skippedInvalidValueCount": 0,
        "skippedMemberIdentifiers": ["EUR", "UNKNOWN"],
    }
    assert {"target_size_mismatch", "target_size_comparison_limited"}.issubset(_codes(result))
    target_size_warning = next(
        warning for warning in result["warnings"] if warning["code"] == "target_size_mismatch"
    )
    assert target_size_warning["memberIdentifiers"] == ["USD-WIDE"]


def test_target_market_cap_without_currency_is_not_compared() -> None:
    result = calculate_peer_diagnostics(
        [_member("USD1", 1_000_000, "USD"), _member("USD2", 2_000_000, "USD")],
        target_context={"marketCap": 2_000_000},
    )
    comparison = result["comparabilityContext"]["targetComparisons"]["marketCap"]

    assert comparison["comparedCount"] == 0
    assert comparison["maximumDifference"] is None
    assert comparison["skippedMissingCurrencyCount"] == 2
    assert "target_size_currency_missing" in _codes(result)
    assert "target_size_mismatch" not in _codes(result)


def test_invalid_and_excluded_market_caps_do_not_create_false_ratios() -> None:
    result = calculate_peer_diagnostics(
        [
            _member("VALID", 1_000_000, "USD"),
            _member("INVALID", -20_000_000, "USD"),
            _member("EXCLUDED", 100_000_000, "USD", included=False),
        ]
    )
    context = result["comparabilityContext"]

    assert "invalid_market_cap_context" in _codes(result)
    assert "wide_size_dispersion" not in _codes(result)
    assert context["invalidMarketCapMemberIdentifiers"] == ["INVALID"]
    assert context["marketCapGroups"]["USD"]["memberIdentifiers"] == ["VALID"]


def test_absent_market_caps_have_explicit_empty_comparison_state() -> None:
    result = calculate_peer_diagnostics(
        [_member("ONE", None, "USD"), _member("TWO", None, None)]
    )
    context = result["comparabilityContext"]

    assert context["coverage"]["marketCap"] == 0
    assert context["marketCapGroups"] == {}
    assert context["marketCapRatio"] is None
    assert context["unusableMarketCapMemberIdentifiers"] == []
    assert context["invalidMarketCapMemberIdentifiers"] == []


def test_diagnostic_acknowledgement_hash_is_deterministic_and_input_bound() -> None:
    members = [
        _member("ONE", 1_000_000, "USD"),
        _member("TWO", 2_000_000, "USD"),
        _member("THREE", 3_000_000, "USD"),
    ]
    as_of = date(2026, 9, 5)

    first = calculate_peer_diagnostics(members, as_of=as_of)
    second = calculate_peer_diagnostics(members, as_of=as_of)
    changed = calculate_peer_diagnostics(
        [{**members[0], "marketCap": 40_000_000}, *members[1:]],
        as_of=as_of,
    )

    assert len(first["acknowledgementSha256"]) == 64
    assert first["acknowledgementSha256"] == second["acknowledgementSha256"]
    assert first["acknowledgementSha256"] != changed["acknowledgementSha256"]
    assert first["warningCodes"] == sorted({item["code"] for item in first["warnings"]})
