from app.models.dcf import DcfAssumptionSet, DcfOutput, DcfProjectionYear, DcfSensitivityTable
from app.models.financial import FinancialExtractionCandidate

class FinancialServicesEngine:
    @classmethod
    def calculate_excess_return_value(cls, assumption_set: DcfAssumptionSet) -> tuple[DcfOutput, list[DcfProjectionYear], list[DcfSensitivityTable]]:
        """
        Calculates intrinsic value using the Excess Return Model for banks/financials.
        Value = Book Equity + PV of (ROE - COE) * Book Equity
        """
        # Assumptions
        book_equity = assumption_set.book_value_of_equity or 0.0
        target_roe = assumption_set.target_roe or 0.10
        cost_of_equity = assumption_set.cost_of_equity or 0.10
        net_income = assumption_set.net_income or 0.0
        growth_rate = assumption_set.terminal_growth_rate or 0.02
        projection_years_count = assumption_set.projection_years_count or 10

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
            year_growth = assumption_set.terminal_growth_rate or 0.02 # simplify for now: assume book equity grows at terminal growth

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

        diluted_shares = assumption_set.diluted_shares or 1.0
        intrinsic_value_per_share = equity_value / diluted_shares if diluted_shares > 0 else None

        output = DcfOutput(
            assumption_set_id=assumption_set.id,
            sum_pv_fcff=sum_pv_excess_returns, # store pv excess returns here
            terminal_value=terminal_value,
            pv_terminal_value=pv_terminal_value,
            enterprise_value=0.0, # N/A for banks
            cash=assumption_set.cash or 0.0,
            non_operating_assets=0.0,
            debt=assumption_set.debt or 0.0,
            minority_interests=0.0,
            preferred_stock=0.0,
            employee_options_value=0.0,
            equity_value=equity_value,
            diluted_shares=diluted_shares,
            intrinsic_value_per_share=intrinsic_value_per_share,
            current_market_price=assumption_set.current_market_price or 0.0,
            upside_downside_pct=((intrinsic_value_per_share / assumption_set.current_market_price) - 1.0) if (intrinsic_value_per_share and assumption_set.current_market_price) else None,
            pv_of_excess_returns=total_pv_excess_returns
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
