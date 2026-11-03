import pytest
from app.models.dcf import DcfAssumptionSet
from app.services.dcf import build_fcff_forecast, calculate_terminal_value
from app.services.fcfe_ddm_engine import FCFEEngine
from app.services.reverse_dcf_engine import MarketImpliedAssumptionSolver
from app.services.wacc_engine import WaccService
def test_fcff_calculations():
    assumption_set = DcfAssumptionSet(
        starting_revenue=1000.0,
        current_operating_margin=0.10,
        target_operating_margin=0.20,
        tax_rate=0.25,
        sales_to_capital_ratio=2.0,
        starting_invested_capital=500.0,
        revenue_growth_years_json={"1": 0.10, "2": 0.10},
        projection_years_count=2
    )

    projection_years, terminal_revenue, terminal_ebit, terminal_nopat = build_fcff_forecast(assumption_set)

    # Year 1
    # Rev = 1100
    # Margin = 0.15 (midpoint of 0.10 and 0.20 for year 1 of 2? Wait, straight line to target? If count=2, yr 1 is 0.15, yr 2 is 0.20)
    assert len(projection_years) == 2
    assert abs(projection_years[0].revenue - 1100.0) < 0.01
    # Reinvestment: delta Rev = 100 / 2.0 = 50.0
    assert abs(projection_years[0].reinvestment - 50.0) < 0.01

    # Year 2
    # Rev = 1210
    assert abs(projection_years[1].revenue - 1210.0) < 0.01
    # Reinvestment: delta Rev = 110 / 2.0 = 55.0
    assert abs(projection_years[1].reinvestment - 55.0) < 0.01


def test_fcfe_calculations():
    assumption_set = DcfAssumptionSet(
        net_income=100.0,
        capex=50.0,
        depreciation=10.0,
        change_in_nwc=5.0,
        new_debt_issued=20.0,
        debt_repaid=5.0
    )
    # fcfe = net_income - (capex - depreciation) - nwc_change + new_debt - debt_repaid
    # fcfe = 100 - (50 - 10) - 5 + 20 - 5 = 100 - 40 - 5 + 20 - 5 = 70
    fcfe = FCFEEngine.calculate_fcfe(assumption_set)
    assert abs(fcfe - 70.0) < 0.01


def test_terminal_value_and_reinvestment():
    assumption_set = DcfAssumptionSet(
        wacc_terminal=0.08,
        terminal_growth_rate=0.03,
        terminal_roic=0.12,
        target_operating_margin=0.20,
        tax_rate=0.25
    )
    # last_revenue = 1000
    # terminal_revenue = 1000 * 1.03 = 1030
    # terminal_ebit = 1030 * 0.20 = 206
    # terminal_nopat = 206 * (1 - 0.25) = 154.5
    # terminal reinvestment rate = 0.03 / 0.12 = 0.25
    # terminal fcff = 154.5 * (1 - 0.25) = 115.875
    # terminal value = 115.875 / (0.08 - 0.03) = 2317.5

    tv, pv_tv, t_fcff = calculate_terminal_value(assumption_set, last_revenue=1000.0, cumulative_discount_factor=1.0)

    assert abs(t_fcff - 115.875) < 0.01
    assert abs(tv - 2317.5) < 0.01


from app.services.wacc_engine import WaccService

def test_wacc_and_beta():
    # WACC: (E/V) * Ke + (D/V) * Kd * (1-T)
    # E/V = 0.6, D/V = 0.4
    # Ke = 0.10, Kd = 0.05, T = 0.20
    # WACC = 0.6 * 0.10 + 0.4 * 0.05 * 0.8 = 0.06 + 0.016 = 0.076
    wacc = WaccService.calculate_wacc(
        cost_of_equity=0.10,
        after_tax_cost_of_debt=0.05 * 0.8,
        equity_weight=0.6,
        debt_weight=0.4
    )
    assert abs(wacc - 0.076) < 0.01


def test_reverse_dcf_solver():
    from app.services.reverse_dcf_engine import MarketImpliedAssumptionSolver
    assumption_set = DcfAssumptionSet(
        starting_revenue=1000.0,
        current_operating_margin=0.15,
        target_operating_margin=0.15,
        tax_rate=0.25,
        sales_to_capital_ratio=2.0,
        starting_invested_capital=500.0,
        revenue_growth_years_json={"1": 0.05, "2": 0.05, "3": 0.05},
        projection_years_count=3,
        wacc_start=0.10,
        wacc_terminal=0.10,
        terminal_growth_rate=0.02,
        terminal_roic=0.10,
        cash=0.0,
        debt=0.0
    )

    # Use a reachable target and require actual convergence, not just a non-null result.
    implied_margin, _, _ = MarketImpliedAssumptionSolver.solve(
        assumption_set=assumption_set,
        target_parameter="target_operating_margin",
        current_market_price=25.0,
        diluted_shares=100.0
    )

    assert implied_margin is not None
    assert implied_margin > 0.0

    # We can test that using this implied margin results in an intrinsic value very close to $100
    test_set = assumption_set
    test_set.target_operating_margin = implied_margin
    test_set.current_market_price = 25.0
    test_set.diluted_shares = 100.0

    from app.services.dcf import calculate_dcf
    output, _, _ = calculate_dcf(test_set)
    assert output.intrinsic_value_per_share is not None
    assert abs(output.intrinsic_value_per_share - 25.0) <= 0.01
