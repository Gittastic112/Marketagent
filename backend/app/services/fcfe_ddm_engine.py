from typing import Any
from app.models.dcf import DcfAssumptionSet
from app.api.schemas import DiagnosticWarning, DcfOutputCreate

class FCFEEngine:
    @classmethod
    def calculate_fcfe(cls, assumption_set: DcfAssumptionSet) -> float | None:
        """Calculate Free Cash Flow to Equity (FCFE)."""
        if assumption_set.net_income is None:
            return None

        net_income = assumption_set.net_income
        capex = assumption_set.capex or 0.0
        depreciation = assumption_set.depreciation or 0.0
        nwc_change = assumption_set.change_in_nwc or 0.0

        fcfe_before_debt = net_income - (capex - depreciation) - nwc_change

        new_debt = assumption_set.new_debt_issued or 0.0
        debt_repaid = assumption_set.debt_repaid or 0.0

        fcfe_after_debt = fcfe_before_debt + new_debt - debt_repaid
        return fcfe_after_debt

    @classmethod
    def calculate_fcfe_intrinsic_value(cls, assumption_set: DcfAssumptionSet, fcfe: float) -> float | None:
        """Simple Gordon Growth Model using FCFE instead of Dividends."""
        cost_of_equity = assumption_set.wacc_terminal or 0.10 # Ideally cost of equity, WACC is a proxy for now
        growth_rate = assumption_set.terminal_growth_rate or 0.02
        diluted_shares = assumption_set.diluted_shares or 1.0

        if cost_of_equity <= growth_rate or fcfe <= 0:
            return None

        equity_value = (fcfe * (1 + growth_rate)) / (cost_of_equity - growth_rate)
        return equity_value / diluted_shares if diluted_shares > 0 else None

class DividendDiscountEngine:
    @classmethod
    def calculate_ddm_intrinsic_value(cls, assumption_set: DcfAssumptionSet) -> float | None:
        """Gordon Growth Model using Dividends."""
        dividends = assumption_set.dividends
        if not dividends or dividends <= 0:
            return None

        cost_of_equity = assumption_set.wacc_terminal or 0.10 # Proxy
        growth_rate = assumption_set.terminal_growth_rate or 0.02
        diluted_shares = assumption_set.diluted_shares or 1.0

        if cost_of_equity <= growth_rate:
            return None

        equity_value = (dividends * (1 + growth_rate)) / (cost_of_equity - growth_rate)
        return equity_value / diluted_shares if diluted_shares > 0 else None

class CompanyCashReturnService:
    @classmethod
    def calculate_net_cash_returned(cls, assumption_set: DcfAssumptionSet) -> float:
        dividends = assumption_set.dividends or 0.0
        buybacks = assumption_set.buybacks or 0.0
        stock_issuances = assumption_set.stock_issuances or 0.0
        return dividends + buybacks - stock_issuances

class PayoutPolicyDiagnosticService:
    @classmethod
    def run_diagnostics(cls, assumption_set: DcfAssumptionSet, fcfe: float | None, output: DcfOutputCreate) -> list[DiagnosticWarning]:
        warnings = []

        dividends = assumption_set.dividends or 0.0
        net_income = assumption_set.net_income

        # [x] Dividend paid despite negative earnings
        if dividends > 0 and net_income is not None and net_income < 0:
            warnings.append(DiagnosticWarning(
                severity="warning",
                module="payout_policy",
                message="Dividends are being paid despite negative Net Income. This is unsustainable.",
                affectedAssumptions=["dividends", "net_income"],
                suggestedFix="Check if the dividend is a special one-time event, or if earnings are temporarily depressed."
            ))

        # [x] Dividend exceeds FCFE
        if fcfe is not None and dividends > fcfe:
            warnings.append(DiagnosticWarning(
                severity="warning",
                module="payout_policy",
                message=f"Dividends (${dividends:,.2f}) exceed Free Cash Flow to Equity (${fcfe:,.2f}). The company is borrowing or drawing down cash to pay dividends.",
                affectedAssumptions=["dividends", "capex", "new_debt_issued"]
            ))

        net_cash_returned = CompanyCashReturnService.calculate_net_cash_returned(assumption_set)

        # [x] Net cash returned exceeds FCFE
        if fcfe is not None and net_cash_returned > fcfe and net_cash_returned > 0:
             warnings.append(DiagnosticWarning(
                severity="watch",
                module="payout_policy",
                message=f"Net Cash Returned (${net_cash_returned:,.2f}) exceeds FCFE (${fcfe:,.2f}). Total shareholder return cannot be sustained at this level without debt issuance or asset sales.",
                affectedAssumptions=["dividends", "buybacks"]
            ))

        buybacks = assumption_set.buybacks or 0.0
        stock_issuances = assumption_set.stock_issuances or 0.0

        # [x] Buybacks offset by stock issuance
        if buybacks > 0 and stock_issuances > (buybacks * 0.5):
            warnings.append(DiagnosticWarning(
                severity="watch",
                module="payout_policy",
                message=f"Stock buybacks (${buybacks:,.2f}) are heavily offset by new stock issuances (${stock_issuances:,.2f}). This may be masking stock-based compensation dilution.",
                affectedAssumptions=["buybacks", "stock_issuances"]
            ))

        # [x] Buybacks when current price > intrinsic value
        current_price = assumption_set.current_market_price or 0.0
        intrinsic_value = output.intrinsic_value_per_share or 0.0

        if buybacks > 0 and current_price > 0 and intrinsic_value > 0 and current_price > intrinsic_value:
             warnings.append(DiagnosticWarning(
                severity="warning",
                module="payout_policy",
                message=f"The company is executing buybacks while its current price (${current_price:,.2f}) exceeds intrinsic value (${intrinsic_value:,.2f}). This destroys shareholder value.",
                affectedAssumptions=["buybacks"],
                suggestedFix="Review if the company lacks reinvestment opportunities or if intrinsic value assumptions are too conservative."
            ))

        return warnings
