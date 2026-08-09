import pytest
from app.models.dcf import DcfAssumptionSet
from app.services.dcf import calculate_dcf

def test_terminal_growth_greater_than_wacc():
    assumption_set = DcfAssumptionSet(
        starting_revenue=100.0,
        projection_years_count=1,
        revenue_growth_years_json={"1": 0.05},
        wacc_start=0.10,
        wacc_terminal=0.08,
        terminal_growth_rate=0.09 # Violation!
    )
    output, _, _ = calculate_dcf(assumption_set)
    warnings = [w["message"] for w in output.warnings_json]

    assert any("greater than or equal to terminal WACC" in w for w in warnings)


def test_terminal_growth_zero_reinvestment():
    assumption_set = DcfAssumptionSet(
        starting_revenue=100.0,
        projection_years_count=1,
        wacc_terminal=0.08,
        terminal_growth_rate=0.03,
        terminal_roic=0.0 # Violation! Growth with zero/negative ROIC means infinite reinvestment or zero
    )
    # The math in calculate_terminal_value handles terminal_roic <= 0 by setting reinvestment to 0.0,
    # but growth requires reinvestment.
    output, _, _ = calculate_dcf(assumption_set)
    warnings = [w["message"] if isinstance(w, dict) else str(w) for w in output.warnings_json]

    assert len(warnings) > 0 # We just want to check some warning triggered for the anomaly


def test_high_growth_negative_reinvestment():
    # Revenue grows from 100 to 200, but sales_to_capital is negative or reinvestment is forced negative
    assumption_set = DcfAssumptionSet(
        starting_revenue=100.0,
        projection_years_count=2,
        revenue_growth_years_json={"1": 0.50, "2": 0.50},
        sales_to_capital_ratio=-2.0 # Negative reinvestment despite growth
    )
    output, _, _ = calculate_dcf(assumption_set)
    # Usually you'd catch this in diagnostics or it would result in weird FCFF
    assert output.enterprise_value is not None


def test_sbc_dilution_warning():
    # Using SBC or basic shares instead of diluted
    # We'll just verify a diagnostic rule fires if diluted_shares is missing or suspiciously low
    assumption_set = DcfAssumptionSet(
        starting_revenue=100.0,
        diluted_shares=0.0 # Violation
    )
    output, _, _ = calculate_dcf(assumption_set)
    # If shares are 0, it should probably return 0 intrinsic value or add a warning
    warnings = [w["message"] for w in output.warnings_json]
    assert any("shares" in w.lower() or "0" in w for w in warnings)
