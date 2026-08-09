import pytest
from app.models.dcf import DcfAssumptionSet, DcfOutput
from app.services.distressed_engine import DistressedCompanyEngine
from app.services.financial_services_engine import FinancialServicesEngine
from app.services.dcf import calculate_dcf

def test_financial_services_engine():
    # Setup assumption set for a bank
    aset = DcfAssumptionSet(
        id=1,
        valuation_model_id=1,
        scenario="Base",
        book_value_of_equity=100.0,
        target_roe=0.15,
        cost_of_equity=0.10,
        net_income=12.0, # current ROE = 12%
        terminal_growth_rate=0.03,
        projection_years_count=5,
        diluted_shares=10.0
    )

    # Calculate excess return
    output, projections, _ = FinancialServicesEngine.calculate_excess_return_value(aset)

    assert len(projections) == 5
    assert output.equity_value is not None
    assert output.intrinsic_value_per_share is not None
    assert output.intrinsic_value_per_share == output.equity_value / 10.0

    # Intrinsic value should be greater than book value per share (10.0) since target ROE > COE
    assert output.intrinsic_value_per_share > 10.0

def test_distressed_company_engine():
    aset = DcfAssumptionSet(
        id=2,
        valuation_model_id=2,
        scenario="Base",
        probability_of_failure=0.30,
        distress_sale_proceeds=50.0,
        diluted_shares=10.0
    )

    # Create a dummy base output
    base_output = DcfOutput(
        assumption_set_id=2,
        equity_value=1000.0,
        intrinsic_value_per_share=100.0
    )

    # Apply distress logic
    distressed_output = DistressedCompanyEngine.calculate_distressed_value(aset, base_output)

    # Expected value = (1000 * 0.70) + (50 * 0.30) = 700 + 15 = 715
    # Expected per share = 715 / 10 = 71.5
    assert distressed_output.base_dcf_value == 1000.0
    assert abs(distressed_output.equity_value - 715.0) < 0.01
    assert abs(distressed_output.intrinsic_value_per_share - 71.5) < 0.01

def test_calculate_dcf_routing():
    aset_bank = DcfAssumptionSet(
        id=3,
        valuation_model_id=3,
        scenario="Base",
        book_value_of_equity=100.0,
        target_roe=0.15,
        cost_of_equity=0.10,
        net_income=12.0,
        terminal_growth_rate=0.03,
        projection_years_count=5,
        diluted_shares=10.0
    )

    output_bank, _, _ = calculate_dcf(aset_bank, model_type="financial_services")
    assert output_bank.pv_of_excess_returns is not None

    # Distressed requires full standard DCF setup for the base value, so testing it here
    # might require mocking `build_fcff_forecast` or supplying all standard fields.
    # We will just verify it does not blow up for a simple standard mock.
