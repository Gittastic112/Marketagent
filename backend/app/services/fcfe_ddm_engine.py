"""Supplementary one-stage equity estimates from complete, explicit saved inputs."""
import math

from app.models.dcf import DcfAssumptionSet
from app.schemas.valuation_outputs import DiagnosticWarning, DcfOutputCreate


FCFE_FIELDS = ("net_income", "capex", "depreciation", "change_in_nwc", "new_debt_issued", "debt_repaid")
GORDON_FIELDS = ("cost_of_equity", "terminal_growth_rate", "diluted_shares")


def _finite(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _gordon_value(assumptions: DcfAssumptionSet, cash_flow: float | None) -> float | None:
    """One-stage estimate from explicit current equity cash flow, rate, growth and shares."""
    rate, growth, shares = (getattr(assumptions, field) for field in GORDON_FIELDS)
    if (not all(_finite(value) for value in (cash_flow, rate, growth, shares))
            or cash_flow < 0 or not 0 <= rate <= 1 or not -.2 <= growth <= .2
            or rate <= growth or shares <= 0):
        return None
    value = cash_flow * (1 + growth) / (rate - growth) / shares
    return value if math.isfinite(value) else None


class FCFEEngine:
    @classmethod
    def calculate_fcfe(cls, assumption_set: DcfAssumptionSet) -> float | None:
        """Calculate Free Cash Flow to Equity (FCFE)."""
        if not all(_finite(getattr(assumption_set, field)) for field in FCFE_FIELDS):
            return None

        net_income = assumption_set.net_income
        capex = assumption_set.capex
        depreciation = assumption_set.depreciation
        nwc_change = assumption_set.change_in_nwc

        fcfe_before_debt = net_income - (capex - depreciation) - nwc_change

        new_debt = assumption_set.new_debt_issued
        debt_repaid = assumption_set.debt_repaid

        fcfe_after_debt = fcfe_before_debt + new_debt - debt_repaid
        return fcfe_after_debt if math.isfinite(fcfe_after_debt) else None

    @classmethod
    def calculate_fcfe_intrinsic_value(cls, assumption_set: DcfAssumptionSet, fcfe: float) -> float | None:
        """Simple Gordon Growth Model using FCFE instead of Dividends."""
        return _gordon_value(assumption_set, fcfe)


class DividendDiscountEngine:
    @classmethod
    def calculate_ddm_intrinsic_value(cls, assumption_set: DcfAssumptionSet) -> float | None:
        """Gordon Growth Model using Dividends."""
        return _gordon_value(assumption_set, assumption_set.dividends)


class CompanyCashReturnService:
    @classmethod
    def calculate_net_cash_returned(cls, assumption_set: DcfAssumptionSet) -> float | None:
        dividends, buybacks, stock_issuances = (assumption_set.dividends, assumption_set.buybacks, assumption_set.stock_issuances)
        if not all(_finite(value) for value in (dividends, buybacks, stock_issuances)):
            return None
        result = dividends + buybacks - stock_issuances
        return result if math.isfinite(result) else None


class PayoutPolicyDiagnosticService:
    @classmethod
    def run_diagnostics(cls, assumption_set: DcfAssumptionSet, fcfe: float | None, output: DcfOutputCreate) -> list[DiagnosticWarning]:
        warnings = []

        for label, fields, result in (
            ("FCFE", FCFE_FIELDS, output.fcfe_intrinsic_value_per_share),
            ("DDM", ("dividends",), output.ddm_intrinsic_value_per_share),
        ):
            if any(getattr(assumption_set, field) is not None for field in fields) and result is None:
                warnings.append(DiagnosticWarning(
                    severity="watch", module="supplementary_equity",
                    message=f"{label} estimate is not available. Supply complete finite cash-flow inputs, explicit cost of equity, terminal growth and positive diluted shares. The one-stage model requires nonnegative cash flow and cost of equity strictly above growth; WACC and missing-value presets are not used.",
                    affectedAssumptions=list(fields + GORDON_FIELDS),
                    suggestedFix="Review the listed inputs and the suitability of a stable-growth equity model; enter zero explicitly where supported by evidence.",
                    formula="Estimate per share = current equity cash flow × (1 + g) / (cost of equity - g) / diluted shares",
                ))

        currency = assumption_set.cash_flow_currency or "currency not configured"
        def amount(value: float) -> str:
            return f"{value:,.2f} {currency}"

        dividends = assumption_set.dividends
        net_income = assumption_set.net_income

        # [x] Dividend paid despite negative earnings
        if _finite(dividends) and dividends > 0 and _finite(net_income) and net_income < 0:
            warnings.append(DiagnosticWarning(
                severity="warning",
                module="payout_policy",
                message="Saved dividend assumptions are positive despite negative net income. Review whether earnings are temporary and how the payout is funded.",
                affectedAssumptions=["dividends", "net_income"],
                suggestedFix="Check if the dividend is a special one-time event, or if earnings are temporarily depressed."
            ))

        # [x] Dividend exceeds FCFE
        if _finite(fcfe) and _finite(dividends) and dividends > fcfe:
            warnings.append(DiagnosticWarning(
                severity="warning",
                module="payout_policy",
                message=f"Saved dividends ({amount(dividends)}) exceed FCFE ({amount(fcfe)}). Review funding and timing; these assumptions do not establish actual borrowing or cash drawdowns.",
                affectedAssumptions=["dividends", "capex", "new_debt_issued"]
            ))

        net_cash_returned = CompanyCashReturnService.calculate_net_cash_returned(assumption_set)

        # [x] Net cash returned exceeds FCFE
        if _finite(fcfe) and net_cash_returned is not None and net_cash_returned > fcfe and net_cash_returned > 0:
            warnings.append(DiagnosticWarning(
                severity="watch",
                module="payout_policy",
                message=f"Saved net cash returned ({amount(net_cash_returned)}) exceeds FCFE ({amount(fcfe)}). Review payout funding and whether these cash flows represent a sustainable period.",
                affectedAssumptions=["dividends", "buybacks"]
            ))

        buybacks = assumption_set.buybacks
        stock_issuances = assumption_set.stock_issuances

        # [x] Buybacks offset by stock issuance
        if _finite(buybacks) and _finite(stock_issuances) and buybacks > 0 and stock_issuances > (buybacks * 0.5):
            warnings.append(DiagnosticWarning(
                severity="watch",
                module="payout_policy",
                message=f"Saved buybacks ({amount(buybacks)}) are substantially offset by stock issuances ({amount(stock_issuances)}). Review issuance sources and the diluted share count; this does not establish stock-based compensation as the cause.",
                affectedAssumptions=["buybacks", "stock_issuances"]
            ))

        # [x] Buybacks when current price > intrinsic value
        current_price = assumption_set.current_market_price
        intrinsic_value = output.intrinsic_value_per_share

        if all(_finite(value) for value in (buybacks, current_price, intrinsic_value)) and buybacks > 0 and current_price > 0 and intrinsic_value >= 0 and current_price > intrinsic_value:
            warnings.append(DiagnosticWarning(
                severity="warning",
                module="payout_policy",
                message=f"Saved buybacks are positive and the saved comparison price ({amount(current_price)}) exceeds the DCF estimate ({amount(intrinsic_value)}). Review both assumptions; this is not a live price or proof of value destruction.",
                affectedAssumptions=["buybacks"],
                suggestedFix="Review if the company lacks reinvestment opportunities or if intrinsic value assumptions are too conservative."
            ))

        return warnings
