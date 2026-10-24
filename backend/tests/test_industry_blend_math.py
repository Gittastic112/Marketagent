"""Independent ratio checks; no database, provider calls or persisted fixtures."""

from copy import deepcopy

import pytest

from app.services.industry_assumption import IndustryAssumptionService


def _prior(industry, sales_to_capital, margin):
    return {
        "industry": industry,
        "country": "United States",
        "dataVersion": {"activeDatasetFileIds": [1]},
        "revenueGrowthPriors": {"industryHistorical5Y": 0.04},
        "marginPriors": {
            "industryUnadjustedOperatingMargin": margin,
            "suggestedTargetMargin": margin,
        },
        "reinvestmentPriors": {
            "industrySalesToCapital": sales_to_capital,
            "suggestedSalesToCapital": sales_to_capital,
            "industryNetCapexToSales": 0.0,
            "industryWorkingCapitalToSales": -0.02,
        },
        "returnPriors": {
            "industryRoc": 0.15,
            "industryRoe": 0.20,
            "industryRoeAdjustedForRd": 0.18,
            "suggestedTerminalRoc": 0.15,
        },
        "capitalStructurePriors": {"industryDebtSignals": 0.3},
        "financingFlowPriors": {
            "numberOfFirms": 20,
            "dividendsUsdMillions": 500.0,
            "contextOnly": True,
        },
        "sourceSummary": [{"module": "reinvestment", "source_file": industry + ".xls"}],
    }


def _blend(monkeypatch, priors=None, weights=(60.0, 40.0), industries=("A", "B")):
    priors = priors or {"A": _prior("A", 1.0, 0.20), "B": _prior("B", 2.0, 0.10)}
    monkeypatch.setattr(
        IndustryAssumptionService,
        "get_assumption_priors",
        staticmethod(lambda db, country, industry: priors[industry]),
    )
    return IndustryAssumptionService.get_weighted_assumption_priors(
        None,
        "United States",
        [{"segment_name": f"Segment {index}", "industry_name": industry, "weight_percent": weight}
         for index, (industry, weight) in enumerate(zip(industries, weights, strict=True))],
    )


def test_sales_to_capital_aggregates_capital_before_dividing(monkeypatch):
    result = _blend(monkeypatch)
    # Revenue 60 requires capital 60; revenue 40 requires capital 20.
    # Combined revenue/capital is 100/80, not the arithmetic ratio average 1.4.
    assert result["reinvestmentPriors"]["industrySalesToCapital"] == pytest.approx(1.25)
    assert result["reinvestmentPriors"]["suggestedSalesToCapital"] == pytest.approx(1.25)
    assert result["marginPriors"]["suggestedTargetMargin"] == pytest.approx(0.16)


def test_revenue_weights_do_not_establish_capital_or_equity_returns(monkeypatch):
    result = _blend(monkeypatch)
    assert all(value is None for value in result["returnPriors"].values())
    assert all(value is False for value in result["coverage"]["returnPriors"].values())
    assert result["capitalStructurePriors"]["industryDebtSignals"] is None
    assert any("capital or equity weights" in message for message in result["warnings"])


def test_multi_year_growth_is_not_an_arithmetic_average_of_rates(monkeypatch):
    result = _blend(monkeypatch)
    assert all(value is None for value in result["revenueGrowthPriors"].values())
    assert any("compounding" in message for message in result["warnings"])
    assert result["aggregationVersion"] == 2


def test_blend_does_not_inherit_first_industry_absolute_financing_totals(monkeypatch):
    result = _blend(monkeypatch)
    assert result["financingFlowPriors"] == {
        "numberOfFirms": None, "dividendsUsdMillions": None, "contextOnly": True,
    }
    assert any("industry totals" in message for message in result["warnings"])


def test_single_taxonomy_keeps_its_unblended_returns_and_context(monkeypatch):
    result = _blend(monkeypatch, industries=("A", "A"))
    assert result["returnPriors"]["industryRoe"] == 0.20
    assert result["returnPriors"]["industryRoeAdjustedForRd"] == 0.18
    assert result["financingFlowPriors"]["dividendsUsdMillions"] == 500
    assert result["reinvestmentPriors"]["industrySalesToCapital"] == 1.0


@pytest.mark.parametrize("value", [None, 0, -1, float("nan"), float("inf"), True])
def test_invalid_capital_ratio_withholds_entire_blend(monkeypatch, value):
    priors = {"A": _prior("A", 1.0, 0.20), "B": _prior("B", value, 0.10)}
    result = _blend(monkeypatch, priors)
    assert result["reinvestmentPriors"]["industrySalesToCapital"] is None
    assert result["coverage"]["reinvestmentPriors"]["industrySalesToCapital"] is False
    assert any("industrySalesToCapital" in message for message in result["warnings"])


@pytest.mark.parametrize("value", [float("nan"), float("inf"), True])
def test_nonfinite_or_boolean_benchmarks_never_become_priors(monkeypatch, value):
    priors = {"A": _prior("A", 1.0, 0.20), "B": _prior("B", 2.0, value)}
    result = _blend(monkeypatch, priors)
    assert result["marginPriors"]["suggestedTargetMargin"] is None
    assert result["coverage"]["marginPriors"]["suggestedTargetMargin"] is False


@pytest.mark.parametrize("weights", [(float("nan"), 40), (float("inf"), 40), (0, 100), (-10, 110), (True, 99), (60, 30)])
def test_invalid_allocation_weights_are_rejected_before_loading_priors(monkeypatch, weights):
    with pytest.raises(ValueError):
        _blend(monkeypatch, weights=weights)


def test_explicit_zero_and_negative_sales_based_priors_remain_valid(monkeypatch):
    result = _blend(monkeypatch)
    assert result["reinvestmentPriors"]["industryNetCapexToSales"] == 0.0
    assert result["reinvestmentPriors"]["industryWorkingCapitalToSales"] == pytest.approx(-0.02)


def test_accepted_rounded_weights_preserve_a_constant_prior(monkeypatch):
    result = _blend(monkeypatch, weights=(60, 39.999), industries=("A", "A"))
    assert result["marginPriors"]["suggestedTargetMargin"] == pytest.approx(0.20)
    assert result["reinvestmentPriors"]["industrySalesToCapital"] == pytest.approx(1.0)


def test_source_results_are_not_mutated_and_component_provenance_survives(monkeypatch):
    priors = {"A": _prior("A", 1.0, 0.20), "B": _prior("B", 2.0, 0.10)}
    before = deepcopy(priors)
    result = _blend(monkeypatch, priors)
    assert priors == before
    assert [row["industryName"] for row in result["sourceSummary"]] == ["A", "B"]
    assert result["dataVersion"]["activeDatasetFileIds"] == [1]
