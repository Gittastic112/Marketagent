import math
from typing import Dict, Any, List

def norm_cdf(x: float) -> float:
    """Cumulative distribution function for the standard normal distribution."""
    return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

class VolatilityEstimationService:
    @staticmethod
    def calculate_firm_value_volatility(
        equity_vol: float,
        debt_vol: float,
        equity_weight: float,
        debt_weight: float,
        rho: float = 0.50
    ) -> float:
        var = (
            (equity_vol ** 2 * equity_weight ** 2) +
            (debt_vol ** 2 * debt_weight ** 2) +
            (2 * rho * equity_vol * debt_vol * equity_weight * debt_weight)
        )
        return math.sqrt(var)

class RealOptionEligibilityService:
    @staticmethod
    def evaluate(inputs: Dict[str, bool]) -> Dict[str, Any]:
        weights = {
            "has_underlying_asset": 20,
            "has_finite_life": 10,
            "has_clear_exercise_price": 15,
            "has_asymmetric_payoff": 15,
            "has_exclusivity": 25,
            "can_estimate_volatility": 15,
        }

        score = 0
        for k, v in inputs.items():
            if v and k in weights:
                score += weights[k]

        passed = score >= 70
        recommendation = "do_not_add_option_value"
        if score >= 85:
            recommendation = "value_with_option_model"
        elif score >= 60:
            recommendation = "use_decision_tree"
        elif score >= 30:
            recommendation = "qualitative_only"

        warnings = []
        if not inputs.get("has_exclusivity"):
            warnings.append("No clear exclusivity. Real option value may be easily eroded by competitors.")
        if not inputs.get("has_finite_life"):
            warnings.append("Without a finite option life, the premium is hard to quantify correctly.")

        return {
            "eligibilityPassed": passed,
            "eligibilityScore": score,
            "recommendation": recommendation,
            "warnings": warnings
        }

class BlackScholesRealOptionService:
    @staticmethod
    def calculate(
        S: float, K: float, t: float, r: float, sigma: float, y: float,
        option_type: str = "call", exclusivity_score: float = 1.0
    ) -> Dict[str, Any]:
        if (not all(math.isfinite(v) for v in (S, K, t, r, sigma, y, exclusivity_score))
                or not 0 <= exclusivity_score <= 1 or option_type.lower() not in {"call", "put"}):
            raise ValueError("Option inputs must be finite, with a supported type and exclusivity between zero and one.")
        if t <= 0 or sigma <= 0 or K <= 0 or S <= 0:
            raise ValueError("Invalid inputs for Black-Scholes. Ensure S, K, t, and sigma are > 0.")

        d1 = (math.log(S) - math.log(K) + (r - y + (sigma ** 2) / 2) * t) / (sigma * math.sqrt(t))
        d2 = d1 - sigma * math.sqrt(t)

        nd1 = norm_cdf(d1)
        nd2 = norm_cdf(d2)

        if option_type.lower() == "call":
            raw_value = S * math.exp(-y * t) * nd1 - K * math.exp(-r * t) * nd2
        else: # put
            raw_value = K * math.exp(-r * t) * (1 - norm_cdf(d2)) - S * math.exp(-y * t) * (1 - norm_cdf(d1))

        adjusted_value = raw_value * exclusivity_score

        if not all(math.isfinite(v) for v in (d1, d2, raw_value, adjusted_value)):
            raise ValueError("Option calculation must produce finite values.")

        return {
            "d1": d1,
            "d2": d2,
            "nd1": nd1,
            "nd2": nd2,
            "raw_option_value": raw_value,
            "adjusted_option_value": adjusted_value,
            "option_delta": nd1 if option_type.lower() == "call" else (nd1 - 1)
        }

class RealOptionIntegrationService:
    @staticmethod
    def generate_adjusted_output(
        base_dcf_value: float,
        adjusted_option_value: float,
        is_already_counted: bool = False
    ) -> Dict[str, Any]:
        if is_already_counted:
            return {
                "option_adjusted_intrinsic_value": base_dcf_value,
                "warnings": ["Option value is already counted in the base DCF (e.g. through high growth rates). Not adding separately."]
            }

        return {
            "option_adjusted_intrinsic_value": base_dcf_value + adjusted_option_value,
            "warnings": []
        }
