import math

import pytest

from app.services.synthetic_rating_catalog import (
    SYNTHETIC_RATING_CATALOG,
    SYNTHETIC_RATING_SOURCE,
    SyntheticRatingFirmType,
)
from app.services.wacc_engine import (
    CapitalStructureService,
    CostOfDebtService,
    CostOfEquityService,
    SyntheticRatingService,
    WaccService,
)


EXPECTED_RATING_TABLES = {
    SyntheticRatingFirmType.LARGE_NON_FINANCIAL: (
        (-100000.0, 0.199999, "D2/D", 0.19),
        (0.2, 0.649999, "C2/C", 0.16),
        (0.65, 0.799999, "Ca2/CC", 0.1261),
        (0.8, 1.249999, "Caa/CCC", 0.0885),
        (1.25, 1.499999, "B3/B-", 0.0509),
        (1.5, 1.749999, "B2/B", 0.0321),
        (1.75, 1.999999, "B1/B+", 0.0275),
        (2.0, 2.2499999, "Ba2/BB", 0.0184),
        (2.25, 2.49999, "Ba1/BB+", 0.0138),
        (2.5, 2.999999, "Baa2/BBB", 0.0111),
        (3.0, 4.249999, "A3/A-", 0.0089),
        (4.25, 5.499999, "A2/A", 0.0078),
        (5.5, 6.499999, "A1/A+", 0.007),
        (6.5, 8.499999, "Aa2/AA", 0.0055),
        (8.5, 100000.0, "Aaa/AAA", 0.004),
    ),
    SyntheticRatingFirmType.SMALL_OR_RISKY: (
        (-100000.0, 0.499999, "D2/D", 0.19),
        (0.5, 0.799999, "C2/C", 0.16),
        (0.8, 1.249999, "Ca2/CC", 0.1261),
        (1.25, 1.499999, "Caa/CCC", 0.0885),
        (1.5, 1.999999, "B3/B-", 0.0509),
        (2.0, 2.499999, "B2/B", 0.0321),
        (2.5, 2.999999, "B1/B+", 0.0275),
        (3.0, 3.499999, "Ba2/BB", 0.0184),
        (3.5, 3.9999999, "Ba1/BB+", 0.0138),
        (4.0, 4.499999, "Baa2/BBB", 0.0111),
        (4.5, 5.999999, "A3/A-", 0.0089),
        (6.0, 7.499999, "A2/A", 0.0078),
        (7.5, 9.499999, "A1/A+", 0.007),
        (9.5, 12.499999, "Aa2/AA", 0.0055),
        (12.5, 100000.0, "Aaa/AAA", 0.004),
    ),
    SyntheticRatingFirmType.FINANCIAL_SERVICE: (
        (-100000.0, 0.049999, "D2/D", 0.19),
        (0.05, 0.099999, "C2/C", 0.16),
        (0.1, 0.199999, "Ca2/CC", 0.1261),
        (0.2, 0.299999, "Caa/CCC", 0.0885),
        (0.3, 0.399999, "B3/B-", 0.0509),
        (0.4, 0.499999, "B2/B", 0.0321),
        (0.5, 0.599999, "B1/B+", 0.0275),
        (0.6, 0.749999, "Ba2/BB", 0.0184),
        (0.75, 0.899999, "Ba1/BB+", 0.0138),
        (0.9, 1.199999, "Baa2/BBB", 0.0111),
        (1.2, 1.49999, "A3/A-", 0.0089),
        (1.5, 1.99999, "A2/A", 0.0078),
        (2.0, 2.49999, "A1/A+", 0.007),
        (2.5, 2.99999, "Aa2/AA", 0.0055),
        (3.0, 100000.0, "Aaa/AAA", 0.004),
    ),
}


def test_cost_of_equity() -> None:
    coe = CostOfEquityService.calculate(
        risk_free_rate=0.04,
        beta=1.2,
        mature_erp=0.05,
        country_risk_premium=0.02,
        lambda_crp=1.0,
    )
    assert round(coe, 4) == 0.12


def test_synthetic_rating_catalog_matches_all_workbook_rows() -> None:
    actual = {
        firm_type: tuple(
            (band.lower_bound, band.upper_bound, band.rating, band.default_spread)
            for band in bands
        )
        for firm_type, bands in SYNTHETIC_RATING_CATALOG.items()
    }

    assert actual == EXPECTED_RATING_TABLES
    assert SYNTHETIC_RATING_SOURCE.source_as_of == "unknown"
    assert SYNTHETIC_RATING_SOURCE.date_confidence == "low"
    assert SYNTHETIC_RATING_SOURCE.recency_claim_type == "User Assumption"
    assert SYNTHETIC_RATING_SOURCE.sha256 == (
        "45d1f61c67f02fb595661e95ef294e72524a105c9db85ee198a918386d580d3c"
    )


@pytest.mark.parametrize("firm_type", list(SyntheticRatingFirmType))
def test_synthetic_rating_uses_each_exact_lower_boundary(
    firm_type: SyntheticRatingFirmType,
) -> None:
    bands = SYNTHETIC_RATING_CATALOG[firm_type]

    for index, band in enumerate(bands):
        result = SyntheticRatingService.estimate(band.lower_bound, firm_type=firm_type)
        assert result.rating == band.rating
        assert result.default_spread == band.default_spread
        assert result.band_lower_bound == band.lower_bound
        assert result.band_upper_bound == band.upper_bound

        if index > 0:
            just_below = math.nextafter(band.lower_bound, -math.inf)
            prior = SyntheticRatingService.estimate(just_below, firm_type=firm_type)
            assert prior.rating == bands[index - 1].rating


def test_synthetic_rating_matches_workbook_example_and_financial_table() -> None:
    workbook_example = SyntheticRatingService.estimate(
        6.25,
        firm_type=SyntheticRatingFirmType.SMALL_OR_RISKY,
    )
    financial = SyntheticRatingService.estimate(
        3.0,
        firm_type=SyntheticRatingFirmType.FINANCIAL_SERVICE,
    )

    assert (workbook_example.rating, workbook_example.default_spread) == ("A2/A", 0.0078)
    assert (financial.rating, financial.default_spread) == ("Aaa/AAA", 0.004)
    assert workbook_example.claim_type == "Calculation"
    assert workbook_example.catalog_version == SYNTHETIC_RATING_SOURCE.catalog_version


@pytest.mark.parametrize("ratio", [math.nan, math.inf, -math.inf])
def test_synthetic_rating_rejects_non_finite_ratios(ratio: float) -> None:
    with pytest.raises(ValueError, match="finite"):
        SyntheticRatingService.estimate(ratio)


def test_legacy_synthetic_rating_wrapper_remains_compatible() -> None:
    large = SyntheticRatingService.get_rating_and_spread(3.5, is_large_mfg=True)
    small = SyntheticRatingService.get_rating_and_spread(3.5, is_large_mfg=False)

    assert large == ("A3/A-", 0.0089)
    assert small == ("Ba1/BB+", 0.0138)


def test_cost_of_debt() -> None:
    pre_tax = CostOfDebtService.calculate_pre_tax(
        risk_free_rate=0.04,
        default_spread=0.015,
        country_default_spread=0.005,
    )
    assert round(pre_tax, 4) == 0.06

    after_tax = CostOfDebtService.calculate_after_tax(
        pre_tax_cost=0.06,
        marginal_tax_rate=0.25,
    )
    assert round(after_tax, 4) == 0.045


def test_capital_structure() -> None:
    eq_w, db_w = CapitalStructureService.calculate_market_weights(
        market_equity=800.0,
        total_debt=200.0,
    )
    assert eq_w == 0.8
    assert db_w == 0.2

    eq_w, db_w = CapitalStructureService.calculate_market_weights(
        market_equity=-100.0,
        total_debt=50.0,
    )
    assert eq_w == 1.0
    assert db_w == 0.0


def test_wacc_calculation() -> None:
    wacc = WaccService.calculate_wacc(0.10, 0.05, 0.8, 0.2)
    assert round(wacc, 4) == 0.09


def test_wacc_fade() -> None:
    fade = WaccService.calculate_wacc_fade(
        current_wacc=0.10,
        terminal_wacc=0.05,
        years_to_fade=5,
        total_years=10,
    )
    assert len(fade) == 10
    assert fade[0] == 0.10
    assert fade[4] == 0.10
    assert fade[5] == 0.09
    assert fade[6] == 0.08
    assert fade[9] == 0.05
