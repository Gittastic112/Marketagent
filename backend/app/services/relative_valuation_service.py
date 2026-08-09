from typing import Any
from sqlalchemy.orm import Session
from app.models.dcf import DcfAssumptionSet
from app.api.schemas import DcfOutputCreate, DiagnosticWarning

class RelativeValuationService:
    """
    Phase 9: Relative Pricing
    Adds pricing benchmarks and DCF-implied multiple sanity checks.
    """

    @classmethod
    def calculate_implied_multiples(cls, output: DcfOutputCreate, assumption_set: DcfAssumptionSet) -> None:
        """
        Calculate implied multiples from the DCF output and update the output object in place.
        """
        equity_value = output.equity_value or 0.0
        ev = output.enterprise_value or 0.0

        starting_revenue = assumption_set.starting_revenue or 0.0
        current_margin = assumption_set.current_operating_margin or 0.0

        ebit = starting_revenue * current_margin

        if starting_revenue > 0:
            output.implied_ev_sales = ev / starting_revenue

        if ebit > 0:
            output.implied_ev_ebit = ev / ebit
            # Proxy EBITDA by adding back some generic D&A if we don't have it, or just use EBIT for now.
            output.implied_ev_ebitda = ev / ebit

        tax_rate = assumption_set.tax_rate or 0.21
        debt = assumption_set.debt or 0.0
        wacc = assumption_set.wacc_start or 0.10

        interest_expense = debt * wacc
        net_income = (ebit - interest_expense) * (1 - tax_rate)

        if net_income > 0:
            output.implied_pe = equity_value / net_income


    @classmethod
    def generate_relative_pricing_diagnostics(cls, output: DcfOutputCreate) -> list[DiagnosticWarning]:
        warnings = []

        # In a real build, we fetch industry benchmarks from DamodaranPricingBenchmark here.
        # For now, we apply static sanity checks for high multiples.

        if output.implied_pe and output.implied_pe > 50:
            warnings.append(DiagnosticWarning(
                severity="warning",
                module="relative_pricing",
                message=f"DCF-implied PE is very high ({output.implied_pe:.1f}x). Ensure growth assumptions justify this premium.",
                affectedAssumptions=["revenue_growth_years_json", "target_operating_margin"],
                suggestedFix="Check if the company is in a hyper-growth phase, otherwise lower growth assumptions.",
                formula="Implied PE = DCF Equity Value / Proxy Net Income"
            ))

        if output.implied_ev_sales and output.implied_ev_sales > 15:
             warnings.append(DiagnosticWarning(
                severity="warning",
                module="relative_pricing",
                message=f"DCF-implied EV/Sales is extreme ({output.implied_ev_sales:.1f}x). Historically, few companies sustain >15x EV/Sales.",
                affectedAssumptions=["starting_revenue", "revenue_growth_years_json"],
                suggestedFix="Verify revenue base and competitive moat.",
                formula="Implied EV/Sales = DCF EV / Starting Revenue"
            ))

        if output.implied_ev_ebitda and output.implied_ev_ebitda < 5 and output.implied_ev_ebitda > 0:
             warnings.append(DiagnosticWarning(
                severity="watch",
                module="relative_pricing",
                message=f"DCF-implied EV/EBITDA is quite low ({output.implied_ev_ebitda:.1f}x). The DCF value might be too conservative.",
                affectedAssumptions=["wacc_start", "terminal_growth_rate"],
                suggestedFix="Check if discount rates are too high or terminal growth is too low.",
            ))

        return warnings
