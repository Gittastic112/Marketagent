import pytest
from app.models.dcf import DcfAssumptionSet
from app.services.dcf import calculate_dcf

def _run_case(assumption_set: DcfAssumptionSet):
    output, projection_years, sensitivity_table = calculate_dcf(assumption_set)
    assert output is not None
    assert output.intrinsic_value_per_share is not None
    assert len(projection_years) == (assumption_set.projection_years_count or 10)
    return output


def test_stable_mature_company():
    # Low growth, stable margin, ROIC ~ WACC
    assumption_set = DcfAssumptionSet(
        starting_revenue=10000.0,
        current_operating_margin=0.15,
        target_operating_margin=0.15,
        tax_rate=0.25,
        sales_to_capital_ratio=2.0,
        revenue_growth_years_json={"1": 0.03, "2": 0.03, "3": 0.03, "4": 0.03, "5": 0.03},
        projection_years_count=5,
        wacc_start=0.08,
        wacc_terminal=0.08,
        terminal_growth_rate=0.02,
        terminal_roic=0.10,
        cash=500.0,
        debt=2000.0,
        diluted_shares=100.0,
        current_market_price=100.0
    )
    output = _run_case(assumption_set)
    assert output.intrinsic_value_per_share > 0


def test_high_growth_profitable_company():
    # High growth, declining slightly, high margins
    assumption_set = DcfAssumptionSet(
        starting_revenue=1000.0,
        current_operating_margin=0.25,
        target_operating_margin=0.20,
        tax_rate=0.21,
        sales_to_capital_ratio=1.5,
        revenue_growth_years_json={"1": 0.30, "2": 0.25, "3": 0.20, "4": 0.15, "5": 0.10},
        projection_years_count=5,
        wacc_start=0.12,
        wacc_terminal=0.08,
        terminal_growth_rate=0.03,
        terminal_roic=0.15,
        cash=1000.0,
        debt=0.0,
        diluted_shares=50.0,
        current_market_price=200.0
    )
    output = _run_case(assumption_set)
    assert output.intrinsic_value_per_share > 0


def test_loss_making_young_company():
    # High growth, negative current margin, positive target margin
    assumption_set = DcfAssumptionSet(
        starting_revenue=100.0,
        current_operating_margin=-0.50, # -50%
        target_operating_margin=0.15,   # +15%
        tax_rate=0.21,
        sales_to_capital_ratio=2.0,
        revenue_growth_years_json={
            "1": 0.50, "2": 0.40, "3": 0.30, "4": 0.20, "5": 0.15,
            "6": 0.10, "7": 0.08, "8": 0.06, "9": 0.05, "10": 0.04
        },
        projection_years_count=10,
        wacc_start=0.15,
        wacc_terminal=0.08,
        terminal_growth_rate=0.02,
        terminal_roic=0.10,
        cash=50.0,
        debt=10.0,
        diluted_shares=20.0,
        current_market_price=15.0
    )
    output = _run_case(assumption_set)
    # Intrinsic value might be positive or negative depending on exact path,
    # but the engine should not crash.
    assert output is not None


def test_capital_intensive_company():
    # Low sales to capital ratio (needs lots of reinvestment)
    assumption_set = DcfAssumptionSet(
        starting_revenue=5000.0,
        current_operating_margin=0.10,
        target_operating_margin=0.10,
        tax_rate=0.25,
        sales_to_capital_ratio=0.5, # Takes $2 of capital to generate $1 of sales
        revenue_growth_years_json={"1": 0.05, "2": 0.05, "3": 0.05},
        projection_years_count=3,
        wacc_start=0.09,
        wacc_terminal=0.08,
        terminal_growth_rate=0.02,
        terminal_roic=0.06, # Poor ROIC
        cash=100.0,
        debt=3000.0,
        diluted_shares=100.0,
        current_market_price=20.0
    )
    output = _run_case(assumption_set)
    # Warnings about value destruction since ROIC < WACC
    assert output.warnings_json is not None


def test_distressed_company():
    # Negative growth, negative margin, high debt
    assumption_set = DcfAssumptionSet(
        starting_revenue=2000.0,
        current_operating_margin=-0.05,
        target_operating_margin=0.02,
        tax_rate=0.25,
        sales_to_capital_ratio=1.5,
        revenue_growth_years_json={"1": -0.10, "2": -0.05, "3": 0.0},
        projection_years_count=3,
        wacc_start=0.20, # Distress cost of capital
        wacc_terminal=0.10,
        terminal_growth_rate=0.0,
        terminal_roic=0.05,
        cash=20.0,
        debt=4000.0, # Massive debt
        diluted_shares=50.0,
        current_market_price=1.0
    )
    output = _run_case(assumption_set)
    # Equity value might be floored at 0 or very negative before floor
    assert output.equity_value < 0.0 # Our model currently lets it go negative if debt > EV
