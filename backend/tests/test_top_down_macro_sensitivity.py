import pytest

from app.services.top_down_macro_sensitivity import TopDownMacroSensitivityService


PERIODS = [
    {
        "period": "2021",
        "operating_income": 50.0,
        "market_cap": 80.0,
        "total_debt": 20.0,
        "change_in_long_term_bond_rate": 0.0,
        "gdp_growth": 0.0,
        "inflation_change": 0.0,
        "currency_change": 0.0,
    },
    {
        "period": "2022",
        "operating_income": 49.5,
        "market_cap": 78.0,
        "total_debt": 20.0,
        "change_in_long_term_bond_rate": 0.01,
        "gdp_growth": 0.0,
        "inflation_change": 0.0,
        "currency_change": 0.0,
    },
    {
        "period": "2023",
        "operating_income": 48.51,
        "market_cap": 74.08,
        "total_debt": 20.0,
        "change_in_long_term_bond_rate": 0.02,
        "gdp_growth": 0.0,
        "inflation_change": 0.0,
        "currency_change": 0.0,
    },
    {
        "period": "2024",
        "operating_income": 47.0547,
        "market_cap": 68.4352,
        "total_debt": 20.0,
        "change_in_long_term_bond_rate": 0.03,
        "gdp_growth": 0.0,
        "inflation_change": 0.0,
        "currency_change": 0.0,
    },
]


def test_calculates_top_down_duration_from_company_history():
    result = TopDownMacroSensitivityService.calculate(PERIODS, frequency="annual")

    assert result["method"] == "top_down"
    assert result["observation_count"] == 3
    assert result["firm_value"]["rate_slope"] == pytest.approx(-2.0)
    assert result["firm_value"]["duration"] == pytest.approx(2.0)
    assert result["operating_income"]["rate_slope"] == pytest.approx(-1.0)
    assert result["operating_income"]["duration"] == pytest.approx(1.0)
    assert result["confidence_label"] == "low"
    assert "Regression output should be interpreted with caution" in result["warnings"][0]
    assert "Change in Firm Value" in result["formula"]


def test_rejects_top_down_regression_with_too_few_periods():
    with pytest.raises(ValueError, match="At least 3 periods"):
        TopDownMacroSensitivityService.calculate(PERIODS[:2], frequency="annual")
