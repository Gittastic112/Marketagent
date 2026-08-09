from sqlalchemy.orm import Session
from app.models.dcf import DcfAssumptionSet
from app.api.schemas import DiagnosticWarning
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
    def solve(cls, assumption_set: DcfAssumptionSet, target_parameter: str, current_market_price: float, diluted_shares: float) -> tuple[float | None, float | None, list[DiagnosticWarning]]:
        """
        Solves for the implied value of the target_parameter that results in the intrinsic_value_per_share equaling current_market_price.
        Uses a simple bisection search.
        """

        # Determine original value and bounds
        low = 0.0
        high = 1.0
        original_value = 0.0

        if target_parameter == "target_operating_margin":
            original_value = assumption_set.target_operating_margin or 0.0
            low, high = -0.5, 1.0
        elif target_parameter == "revenue_growth":
            # For revenue growth, we'll apply a flat scalar to all projected years
            original_value = 0.10 # dummy original for reference
            if assumption_set.revenue_growth_years_json:
                vals = list(assumption_set.revenue_growth_years_json.values())
                if vals:
                    original_value = sum(float(v) for v in vals) / len(vals)
            low, high = -0.5, 2.0
        elif target_parameter == "wacc_start":
            original_value = assumption_set.wacc_start or 0.10
            low, high = 0.01, 0.50
        elif target_parameter == "terminal_growth_rate":
            original_value = assumption_set.terminal_growth_rate or 0.02
            low, high = -0.10, 0.10
        else:
            return None, None, [DiagnosticWarning(severity="error", module="reverse_dcf", message=f"Unsupported target parameter: {target_parameter}")]

        def evaluate(test_val: float) -> float:
            test_set = copy.deepcopy(assumption_set)
            test_set.diluted_shares = diluted_shares
            test_set.current_market_price = current_market_price

            if target_parameter == "target_operating_margin":
                test_set.target_operating_margin = test_val
            elif target_parameter == "wacc_start":
                test_set.wacc_start = test_val
            elif target_parameter == "terminal_growth_rate":
                test_set.terminal_growth_rate = test_val
            elif target_parameter == "revenue_growth":
                # apply to all years
                years = test_set.revenue_growth_years_json or {}
                new_years = {k: test_val for k in years.keys()}
                if not new_years:
                    new_years = {str(i): test_val for i in range(1, (test_set.projection_years_count or 10) + 1)}
                test_set.revenue_growth_years_json = new_years

            output, _, _ = calculate_dcf(test_set)
            return output.intrinsic_value_per_share

        # Determine direction of relationship
        val_low = evaluate(low)
        val_high = evaluate(high)

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

        # If we didn't converge within 0.01, return best effort or None
        final_mid = (low + high) / 2
        diagnostics = ReverseDCFDiagnosticsService.generate_diagnostics(target_parameter, final_mid, original_value)
        diagnostics.append(DiagnosticWarning(
            severity="warning",
            module="reverse_dcf",
            message="Solver reached iteration limit. The returned value is an approximation and might not perfectly hit the market price."
        ))
        return final_mid, original_value, diagnostics
