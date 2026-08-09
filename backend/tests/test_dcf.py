import pytest
from pydantic import ValidationError

from app.api.schemas import DcfAssumptionSetWrite
from app.models.dcf import DcfAssumptionSet
from app.services.dcf import calculate_dcf

def test_calculate_dcf_deterministic_math():
    assumption_set = DcfAssumptionSet(
        id=1,
        valuation_model_id=1,
        scenario="Base",
        starting_revenue=1000.0,
        current_operating_margin=0.10,
        target_operating_margin=0.15,
        tax_rate=0.25,
        sales_to_capital_ratio=2.0,
        starting_invested_capital=500.0,
        revenue_growth_years_json={"1": 0.10, "2": 0.10, "3": 0.05, "4": 0.05, "5": 0.05},
        projection_years_count=5,
        wacc_start=0.10,
        wacc_terminal=0.08,
        terminal_growth_rate=0.02,
        terminal_roic=0.08,
        cash=50.0,
        debt=200.0,
        diluted_shares=100.0,
        current_market_price=10.0
    )

    output, projection_years, sensitivity_tables = calculate_dcf(assumption_set)

    assert len(projection_years) == 5
    # Year 1 revenue: 1000 * 1.1 = 1100
    assert abs(projection_years[0].revenue - 1100.0) < 0.01

    # Reinvestment year 1: (1100 - 1000) / 2.0 = 50.0
    assert abs(projection_years[0].reinvestment - 50.0) < 0.01

    # Check that diagnostics ran
    assert isinstance(output.warnings_json, list)
    assert output.enterprise_value > 0
    assert output.equity_value == output.enterprise_value + 50.0 - 200.0


def test_dcf_diagnostics():
    assumption_set = DcfAssumptionSet(
        id=2,
        valuation_model_id=1,
        scenario="Base",
        projection_years_count=1,
        starting_revenue=100.0,
        revenue_growth_years_json={"1": 0.05},
        wacc_start=0.10,
        wacc_terminal=0.08,
        terminal_growth_rate=0.10, # Violates WACC and > 5%
        debt=0.0
    )
    output, _, _ = calculate_dcf(assumption_set)
    warnings = output.warnings_json
    warning_messages = [warning["message"] for warning in warnings]

    assert any("greater than or equal to terminal WACC" in message for message in warning_messages)
    assert any("exceeds 5%" in message for message in warning_messages)
    assert any("Debt is 0" in message for message in warning_messages)


def test_dcf_sensitivity():
    assumption_set = DcfAssumptionSet(
        id=3,
        valuation_model_id=1,
        projection_years_count=1,
        wacc_terminal=0.10,
        terminal_growth_rate=0.02
    )
    output, _, sensitivity_tables = calculate_dcf(assumption_set)
    sensitivity_table = next(
        table for table in sensitivity_tables if table.table_type == "wacc_vs_terminal_growth"
    )

    # 5x5 table around the base assumptions.
    assert len(sensitivity_table.values_json) == 5
    for w_key, row in sensitivity_table.values_json.items():
        assert len(row) == 5


def test_persisted_dcf_contract_rejects_percentage_points_and_invalid_capital_weights():
    with pytest.raises(ValidationError):
        DcfAssumptionSetWrite(
            starting_revenue=1000,
            target_operating_margin=31.3,
            wacc_start=1.08,
            wacc_terminal=1.08,
            debt_to_capital=1.2,
            equity_to_capital=1.8,
            diluted_shares=100,
            current_market_price=10,
        )


def test_persisted_dcf_contract_allows_missing_market_price_comparison():
    assumptions = DcfAssumptionSetWrite(
        starting_revenue=1000,
        starting_invested_capital=500,
        sales_to_capital_ratio=2,
        diluted_shares=100,
        current_market_price=0,
    )

    assert assumptions.current_market_price == 0


def test_dcf_quality_score_penalizes_blocking_unit_errors():
    assumption_set = DcfAssumptionSet(
        id=4,
        valuation_model_id=1,
        projection_years_count=1,
        starting_revenue=1000,
        revenue_growth_years_json={"1": 0.05},
        current_operating_margin=0.20,
        target_operating_margin=31.3,
        tax_rate=0.25,
        sales_to_capital_ratio=2.0,
        wacc_start=1.08,
        wacc_terminal=1.08,
        terminal_growth_rate=0.03,
        terminal_roic=1.08,
        diluted_shares=100,
        current_market_price=10,
    )

    output, _, _ = calculate_dcf(assumption_set)

    assert output.model_quality_score is not None
    assert output.model_quality_score < 50
    assert any(warning["severity"] == "blocking" for warning in output.warnings_json)
