import pytest
import math
from app.services.real_options_service import (
    RealOptionEligibilityService,
    BlackScholesRealOptionService,
    VolatilityEstimationService
)

def test_firm_volatility_calculation():
    # Example: 30% equity vol, 10% debt vol, 60% equity, 40% debt, correlation 0.5
    vol = VolatilityEstimationService.calculate_firm_value_volatility(
        equity_vol=0.30,
        debt_vol=0.10,
        equity_weight=0.60,
        debt_weight=0.40,
        rho=0.50
    )
    # var = (0.3*0.6)^2 + (0.1*0.4)^2 + 2*0.5*0.3*0.1*0.6*0.4
    # var = 0.0324 + 0.0016 + 0.0072 = 0.0412
    # vol = sqrt(0.0412) = 0.20297
    assert math.isclose(vol, 0.20297, rel_tol=1e-3)

def test_eligibility_service():
    # Test passed
    inputs_pass = {
        "has_underlying_asset": True,   # 20
        "has_finite_life": True,        # 10
        "has_clear_exercise_price": True, # 15
        "has_asymmetric_payoff": True,  # 15
        "has_exclusivity": True,        # 25
        "can_estimate_volatility": True # 15
    }
    res_pass = RealOptionEligibilityService.evaluate(inputs_pass)
    assert res_pass["eligibilityPassed"] is True
    assert res_pass["eligibilityScore"] == 100

    # Test failure
    inputs_fail = {
        "has_underlying_asset": True,   # 20
        "has_finite_life": False,
        "has_clear_exercise_price": False,
        "has_asymmetric_payoff": True,  # 15
        "has_exclusivity": False,
        "can_estimate_volatility": False
    }
    res_fail = RealOptionEligibilityService.evaluate(inputs_fail)
    assert res_fail["eligibilityPassed"] is False
    assert res_fail["eligibilityScore"] == 35
    assert len(res_fail["warnings"]) > 0

def test_black_scholes_call():
    # S = 100, K = 100, t = 1, r = 0.05, sigma = 0.2, y = 0
    res = BlackScholesRealOptionService.calculate(
        S=100.0,
        K=100.0,
        t=1.0,
        r=0.05,
        sigma=0.20,
        y=0.0
    )
    # Basic BS call option value should be around 10.45
    assert math.isclose(res["adjusted_option_value"], 10.45, rel_tol=1e-2)
    assert res["option_delta"] > 0.5 and res["option_delta"] < 0.7
