from app.models.dcf import DcfAssumptionSet
from app.services.dcf import calculate_dcf


def test_calculate_dcf_deterministic_math():
    assumption_set = DcfAssumptionSet(
        id=1,
        valuation_model_id=1,
        scenario="Base",
        discount_rate=0.10,
        terminal_growth_rate=0.02,
        projection_years=5,
        assumptions_json={
            "current_fcf": 100.0,
            "shares_outstanding": 10.0,
            "net_debt": 50.0,
            "fcf_growth_rate": 0.05
        }
    )

    output = calculate_dcf(assumption_set)

    assert len(output.output_json["projected_fcfs"]) == 5
    
    # Year 1: 100 * 1.05 = 105
    # Year 2: 105 * 1.05 = 110.25
    # Year 3: 110.25 * 1.05 = 115.7625
    # Year 4: 115.7625 * 1.05 = 121.550625
    # Year 5: 121.550625 * 1.05 = 127.62815625
    assert abs(output.output_json["projected_fcfs"][0] - 105.0) < 0.01
    assert abs(output.output_json["projected_fcfs"][4] - 127.628) < 0.01

    # Terminal value = 127.62815625 * 1.02 / (0.10 - 0.02) = 130.1807 / 0.08 = 1627.258
    assert abs(output.output_json["terminal_value"] - 1627.258) < 0.01

    # PV of TV = 1627.258 / (1.10 ^ 5) = 1627.258 / 1.61051 = 1010.40
    assert abs(output.output_json["pv_terminal_value"] - 1010.40) < 0.01

    # Enterprise Value
    assert output.enterprise_value > 0
    
    # Equity Value
    assert output.equity_value == output.enterprise_value - 50.0

    # Implied Share Price
    assert output.implied_share_price == output.equity_value / 10.0
