from app.models.dcf import DcfAssumptionSet, DcfOutput, DcfProjectionYear, DcfSensitivityTable
from app.models.financial import FinancialExtractionCandidate
from math import isfinite

from app.schemas.valuation_outputs import DiagnosticWarning
from app.services.diagnostics_engine import DiagnosticsEngine


def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)

class FinancialServicesEngine:
    @classmethod
    def calculate_excess_return_value(cls, assumption_set: DcfAssumptionSet) -> tuple[DcfOutput, list[DcfProjectionYear], list[DcfSensitivityTable]]:
        """
        Calculates intrinsic value using the Excess Return Model for banks/financials.
        Value = Book Equity + PV of (ROE - COE) * Book Equity
        """
        def unavailable(fields, message):
            warning = DiagnosticWarning(severity="blocking", module="financial_services_inputs",
                message=message, affectedAssumptions=fields,
                suggestedFix="Review explicit equity-model inputs, currency and monetary/share scale.")
            return DcfOutput(assumption_set_id=assumption_set.id,
                warnings_json=[warning.model_dump()], model_quality_score=0), [], []

        bounds = {"book_value_of_equity": (0, None), "diluted_shares": (0, None),
            "target_roe": (-1, 1), "cost_of_equity": (0, 1),
            "terminal_growth_rate": (-.2, .2), "net_income": (None, None)}
        invalid = []
        for field, (lower, upper) in bounds.items():
            value = getattr(assumption_set, field)
            if (not _finite(value) or (lower is not None and value < lower)
                    or (upper is not None and value > upper)
                    or (field in {"book_value_of_equity", "diluted_shares"} and value == 0)):
                invalid.append(field)
        horizon = assumption_set.projection_years_count
        if isinstance(horizon, bool) or not isinstance(horizon, int) or not 1 <= horizon <= 30:
            invalid.append("projection_years_count")
        if invalid:
            return unavailable(invalid, "Excess-return valuation requires complete finite equity inputs and a valid horizon; missing values are not presets.")
        book_equity = assumption_set.book_value_of_equity
        target_roe = assumption_set.target_roe
        cost_of_equity = assumption_set.cost_of_equity
        net_income = assumption_set.net_income
        growth_rate = assumption_set.terminal_growth_rate
        projection_years_count = horizon
        if cost_of_equity <= growth_rate:
            return unavailable(["cost_of_equity", "terminal_growth_rate"],
                "Terminal growth must be below cost of equity for a convergent excess-return perpetuity.")

        projection_years = []
        last_book_equity = book_equity
        sum_pv_excess_returns = 0.0
        cumulative_discount_factor = 1.0

        current_roe = (net_income / book_equity) if book_equity > 0 else target_roe

        for year in range(1, projection_years_count + 1):
            # Linearly fade ROE to target ROE
            roe_delta = target_roe - current_roe
            roe = current_roe + (roe_delta * (year / projection_years_count))

            # Net Income = ROE * Book Equity
            year_net_income = roe * last_book_equity

            # Assume payout ratio to sustain growth: b = g / ROE
            # If growth > ROE, payout is 0 and they must raise equity. Let's just use constant growth for book equity
            year_growth = growth_rate # Simplified constant book-equity growth, not a payout forecast.

            # Excess Return = (ROE - COE) * Book Equity
            excess_return = (roe - cost_of_equity) * last_book_equity

            cumulative_discount_factor *= (1 + cost_of_equity)
            pv_excess_return = excess_return / cumulative_discount_factor
            sum_pv_excess_returns += pv_excess_return

            proj_year = DcfProjectionYear(
                assumption_set_id=assumption_set.id,
                year_index=year,
                calendar_year=2024 + year,
                revenue=0.0, # Not applicable
                revenue_growth=year_growth,
                ebit_margin=0.0,
                ebit=0.0,
                tax_rate=0.0,
                nopat=year_net_income, # repurpose nopat as net income
                reinvestment=0.0,
                fcff=excess_return, # repurpose fcff as excess return
                invested_capital=last_book_equity, # repurpose IC as Book Equity
                roic=roe, # repurpose roic as roe
                wacc=cost_of_equity,
                discount_factor=cumulative_discount_factor,
                pv_fcff=pv_excess_return
            )
            projection_years.append(proj_year)

            last_book_equity *= (1 + year_growth)

        # Terminal Value of Excess Returns
        # TV = Expected Excess Return in Terminal Year / (COE - g)
        terminal_excess_return = (target_roe - cost_of_equity) * last_book_equity
        if cost_of_equity > growth_rate:
            terminal_value = terminal_excess_return / (cost_of_equity - growth_rate)
        else:
            terminal_value = 0.0

        pv_terminal_value = terminal_value / cumulative_discount_factor

        total_pv_excess_returns = sum_pv_excess_returns + pv_terminal_value
        equity_value = book_equity + total_pv_excess_returns

        diluted_shares = assumption_set.diluted_shares
        intrinsic_value_per_share = equity_value / diluted_shares
        calculated = [equity_value, intrinsic_value_per_share, terminal_value, pv_terminal_value,
            sum_pv_excess_returns, total_pv_excess_returns]
        calculated.extend(getattr(p, field) for p in projection_years for field in
            ("nopat", "fcff", "invested_capital", "roic", "discount_factor", "pv_fcff"))
        if not all(_finite(value) for value in calculated):
            return unavailable(list(bounds), "Excess-return calculation exceeds the supported finite numeric range.")
        price = assumption_set.current_market_price
        price = price if _finite(price) and price > 0 else None
        gap = intrinsic_value_per_share / price - 1 if price is not None else None
        gap = gap if _finite(gap) else None
        warnings = [DiagnosticWarning(severity="watch", module="financial_services_method",
            message="Simplified excess-return estimate: constant book-equity growth and linear ROE fade. Legacy projection fields represent net income, excess return, book equity, ROE and cost of equity, not FCFF operating metrics.",
            affectedAssumptions=["target_roe", "terminal_growth_rate"],
            suggestedFix="Review sustainable capital needs, payout, currency and share scale independently.").model_dump()]

        output = DcfOutput(
            assumption_set_id=assumption_set.id,
            sum_pv_fcff=sum_pv_excess_returns, # store pv excess returns here
            terminal_value=terminal_value,
            pv_terminal_value=pv_terminal_value,
            enterprise_value=None, # Equity model: an enterprise bridge is not applicable.
            equity_value=equity_value,
            diluted_shares=diluted_shares,
            intrinsic_value_per_share=intrinsic_value_per_share,
            current_market_price=price,
            upside_downside_pct=gap,
            pv_of_excess_returns=total_pv_excess_returns,
            warnings_json=warnings,
            model_quality_score=DiagnosticsEngine.quality_score(warnings),
        )

        return output, projection_years, []

    @classmethod
    def evaluate_trust_gates(cls, candidate: FinancialExtractionCandidate) -> bool:
        """
        Stage 4: Trust Gates
        No fact becomes valuation-ready unless required review conditions are satisfied.
        At minimum:
        - source known
        - reporting period known
        - unit known
        - currency known (on period)
        - source locator known where supported
        - review state known
        """
        if not candidate.source_text or not candidate.raw_document_id:
            return False

        if not candidate.fiscal_year or not candidate.period_type:
            return False

        if not candidate.unit:
            return False

        if candidate.review_status != "reviewed":
            return False

        if candidate.source_locator_json is None and not candidate.source_line_number and not candidate.source_table_name:
            # Need some form of locator
            return False

        return True
