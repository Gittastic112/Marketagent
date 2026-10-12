import math
from app.models.dcf import DcfAssumptionSet
from app.schemas.valuation_outputs import DiagnosticWarning
from app.services.dcf import calculate_dcf
import copy

class ReverseDCFDiagnosticsService:
    @classmethod
    def generate_diagnostics(cls, target_parameter: str, implied_value: float, original_value: float) -> list[DiagnosticWarning]:
        warnings = []

        if target_parameter == "target_operating_margin":
            if implied_value > 0.45:
                warnings.append(DiagnosticWarning(
                    severity="warning",
                    module="reverse_dcf",
                    message=f"The market implies a {implied_value*100:.1f}% target operating margin, which is historically extreme for almost any sector.",
                    affectedAssumptions=["target_operating_margin"],
                    suggestedFix="Re-evaluate whether the market price makes sense or if other growth assumptions are too low."
                ))
            elif implied_value < 0:
                warnings.append(DiagnosticWarning(
                    severity="warning",
                    module="reverse_dcf",
                    message="The market implies a negative target operating margin.",
                    affectedAssumptions=["target_operating_margin"]
                ))

        elif target_parameter == "revenue_growth":
            if implied_value > 0.50:
                warnings.append(DiagnosticWarning(
                    severity="warning",
                    module="reverse_dcf",
                    message=f"The market implies {implied_value*100:.1f}% sustained revenue growth, which is extremely high.",
                    affectedAssumptions=["revenue_growth_years_json"]
                ))

        elif target_parameter == "wacc_start":
            if implied_value < 0.05:
                warnings.append(DiagnosticWarning(
                    severity="warning",
                    module="reverse_dcf",
                    message=f"The market implies a very low cost of capital ({implied_value*100:.1f}%).",
                    affectedAssumptions=["wacc_start"]
                ))

        elif target_parameter == "terminal_growth_rate":
            if implied_value > 0.05:
                warnings.append(DiagnosticWarning(
                    severity="warning",
                    module="reverse_dcf",
                    message=f"The market implies a terminal growth rate of {implied_value*100:.1f}%, which likely exceeds long-term GDP growth.",
                    affectedAssumptions=["terminal_growth_rate"]
                ))

        return warnings

class MarketImpliedAssumptionSolver:
    @classmethod
    def evaluate(cls, assumption_set: DcfAssumptionSet, target_parameter: str,
                 value: float, current_market_price: float, diluted_shares: float,
                 model_type: str = "fcff_dcf"):
        # Copy scalar columns only. Never mutate a persistent instance or ORM graph.
        test_set = DcfAssumptionSet(**{column.key: copy.deepcopy(getattr(assumption_set, column.key))
            for column in DcfAssumptionSet.__table__.columns})
        test_set.diluted_shares = diluted_shares
        test_set.current_market_price = current_market_price
        if target_parameter == "revenue_growth":
            test_set.revenue_growth_years_json = {
                str(year): value for year in range(1, (test_set.projection_years_count or 10) + 1)
            }
        else:
            setattr(test_set, target_parameter, value)
        return calculate_dcf(test_set, model_type=model_type, include_sensitivity=False)[0]

    @classmethod
    def solve(cls, assumption_set: DcfAssumptionSet, target_parameter: str, current_market_price: float, diluted_shares: float, model_type: str = "fcff_dcf") -> tuple[float | None, float | None, list[DiagnosticWarning]]:
        """
        Solves for the implied value of the target_parameter that results in the intrinsic_value_per_share equaling current_market_price.
        Uses a simple bisection search.
        """

        # Determine original value and bounds
        low = 0.0
        high = 1.0
        original_value = 0.0

        if target_parameter == "target_operating_margin":
            original_value = assumption_set.target_operating_margin
            low, high = -0.5, 1.0
        elif target_parameter == "revenue_growth":
            # For revenue growth, we'll apply a flat scalar to all projected years
            years = assumption_set.projection_years_count or 10
            growth = assumption_set.revenue_growth_years_json or {}
            original_value = sum(float(growth.get(str(i), 0)) for i in range(1, years + 1)) / years
            low, high = -0.5, 2.0
        elif target_parameter == "wacc_start":
            original_value = assumption_set.wacc_start
            low, high = 0.01, 0.50
        elif target_parameter == "terminal_growth_rate":
            original_value = assumption_set.terminal_growth_rate
            low, high = -0.10, min(0.10, (assumption_set.wacc_terminal or 0.10) - 0.0001)
        else:
            return None, None, [DiagnosticWarning(severity="blocking", module="reverse_dcf", message="Unsupported target parameter")]

        def evaluate(test_val: float) -> float:
            output = cls.evaluate(assumption_set, target_parameter, test_val,
                current_market_price, diluted_shares, model_type)
            value = output.intrinsic_value_per_share
            if value is None or not math.isfinite(value):
                raise ValueError("Reverse DCF produced a nonfinite value")
            return value

        # Determine direction of relationship
        val_low = evaluate(low)
        val_high = evaluate(high)
        for bound, value in ((low, val_low), (high, val_high)):
            if abs(value - current_market_price) <= 0.01:
                return bound, original_value, ReverseDCFDiagnosticsService.generate_diagnostics(target_parameter, bound, original_value)
        if not min(val_low, val_high) < current_market_price < max(val_low, val_high):
            return None, original_value, [DiagnosticWarning(severity="blocking", module="reverse_dcf",
                message=f"No bracketed solution in the searched range [{low:.4f}, {high:.4f}]. No implied value is reported; this is not proof that no other solution exists.")]

        # If the parameter has an inverse relationship (like WACC), val_low > val_high.
        # Bisection search
        for _ in range(50):
            mid = (low + high) / 2
            val_mid = evaluate(mid)

            if abs(val_mid - current_market_price) < 0.01:
                diagnostics = ReverseDCFDiagnosticsService.generate_diagnostics(target_parameter, mid, original_value)
                return mid, original_value, diagnostics

            if val_high > val_low:
                # Direct relationship (e.g. margin -> value)
                if val_mid < current_market_price:
                    low = mid
                else:
                    high = mid
            else:
                # Inverse relationship (e.g. wacc -> value)
                if val_mid > current_market_price:
                    low = mid
                else:
                    high = mid

        return None, original_value, [DiagnosticWarning(severity="blocking", module="reverse_dcf",
            message="Solver did not reach the requested price within 0.01 currency units. No implied value is reported.")]
