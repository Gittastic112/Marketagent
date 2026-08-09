from app.models.dcf import DcfAssumptionSet, DcfOutput, DcfProjectionYear, DcfSensitivityTable
from app.services.financial_services_engine import FinancialServicesEngine
from app.services.distressed_engine import DistressedCompanyEngine
from copy import deepcopy

def build_fcff_forecast(assumption_set: DcfAssumptionSet) -> tuple[list[DcfProjectionYear], float, float, float]:
    starting_revenue = assumption_set.starting_revenue or 0.0
    current_operating_margin = assumption_set.current_operating_margin or 0.0
    target_operating_margin = assumption_set.target_operating_margin or current_operating_margin
    tax_rate = assumption_set.tax_rate or 0.21
    sales_to_capital_ratio = assumption_set.sales_to_capital_ratio or 1.0
    starting_invested_capital = assumption_set.starting_invested_capital or 0.0
    revenue_growth_years = assumption_set.revenue_growth_years_json or {}
    wacc_start = assumption_set.wacc_start or 0.10
    wacc_terminal = assumption_set.wacc_terminal or wacc_start
    projection_years_count = assumption_set.projection_years_count or 10

    projection_years = []
    last_revenue = starting_revenue
    last_invested_capital = starting_invested_capital
    sum_pv_fcff = 0.0
    cumulative_discount_factor = 1.0

    for year in range(1, projection_years_count + 1):
        growth_rate_str = str(year)
        growth_rate = float(revenue_growth_years.get(growth_rate_str, 0.0))

        revenue = last_revenue * (1 + growth_rate)

        margin_delta = target_operating_margin - current_operating_margin
        ebit_margin = current_operating_margin + (margin_delta * (year / projection_years_count))

        ebit = revenue * ebit_margin
        nopat = ebit * (1 - tax_rate)

        revenue_change = revenue - last_revenue
        reinvestment = (revenue_change / sales_to_capital_ratio) if sales_to_capital_ratio > 0 else 0.0

        fcff = nopat - reinvestment

        invested_capital = last_invested_capital + reinvestment
        roic = nopat / last_invested_capital if last_invested_capital > 0 else 0.0

        if year > (projection_years_count / 2):
            wacc_delta = wacc_terminal - wacc_start
            fade_years = projection_years_count - (projection_years_count / 2)
            wacc = wacc_start + wacc_delta * ((year - (projection_years_count / 2)) / fade_years)
        else:
            wacc = wacc_start

        cumulative_discount_factor *= (1 + wacc)
        pv_fcff = fcff / cumulative_discount_factor
        sum_pv_fcff += pv_fcff

        proj_year = DcfProjectionYear(
            assumption_set_id=assumption_set.id,
            year_index=year,
            calendar_year=2024 + year,
            revenue=revenue,
            revenue_growth=growth_rate,
            ebit_margin=ebit_margin,
            ebit=ebit,
            tax_rate=tax_rate,
            nopat=nopat,
            reinvestment=reinvestment,
            fcff=fcff,
            invested_capital=invested_capital,
            roic=roic,
            wacc=wacc,
            discount_factor=cumulative_discount_factor,
            pv_fcff=pv_fcff
        )
        projection_years.append(proj_year)

        last_revenue = revenue
        last_invested_capital = invested_capital

    return projection_years, sum_pv_fcff, last_revenue, cumulative_discount_factor


def calculate_terminal_value(assumption_set: DcfAssumptionSet, last_revenue: float, cumulative_discount_factor: float) -> tuple[float, float, float]:
    target_operating_margin = assumption_set.target_operating_margin or (assumption_set.current_operating_margin or 0.0)
    tax_rate = assumption_set.tax_rate or 0.21
    terminal_growth_rate = assumption_set.terminal_growth_rate or 0.02
    terminal_roic = assumption_set.terminal_roic or (assumption_set.wacc_terminal or 0.10)
    wacc_terminal = assumption_set.wacc_terminal or 0.10

    terminal_reinvestment_rate = (terminal_growth_rate / terminal_roic) if terminal_roic > 0 else 0.0

    terminal_revenue = last_revenue * (1 + terminal_growth_rate)
    terminal_ebit = terminal_revenue * target_operating_margin
    terminal_nopat = terminal_ebit * (1 - tax_rate)
    terminal_fcff = terminal_nopat * (1 - terminal_reinvestment_rate)

    if wacc_terminal > terminal_growth_rate:
        terminal_value = terminal_fcff / (wacc_terminal - terminal_growth_rate)
    else:
        terminal_value = 0.0

    pv_terminal_value = terminal_value / cumulative_discount_factor
    return terminal_value, pv_terminal_value, terminal_fcff


def calculate_equity_bridge(assumption_set: DcfAssumptionSet, enterprise_value: float) -> tuple[float, float, float]:
    cash = assumption_set.cash or 0.0
    debt = assumption_set.debt or 0.0
    minority_interests = assumption_set.minority_interests or 0.0
    preferred_stock = assumption_set.preferred_stock or 0.0
    employee_options_value = assumption_set.employee_options_value or 0.0
    cross_holdings = assumption_set.cross_holdings or 0.0
    operating_leases = assumption_set.operating_leases or 0.0
    diluted_shares = assumption_set.diluted_shares or 1.0
    current_market_price = assumption_set.current_market_price or 0.0

    equity_value = enterprise_value + cash + cross_holdings - debt - operating_leases - minority_interests - preferred_stock - employee_options_value
    intrinsic_value_per_share = equity_value / diluted_shares if diluted_shares > 0 else 0.0
    upside_downside_pct = (intrinsic_value_per_share / current_market_price - 1) if current_market_price > 0 else 0.0

    return equity_value, intrinsic_value_per_share, upside_downside_pct


from typing import Any
from app.services.diagnostics_engine import DiagnosticsEngine
from app.services.relative_valuation_service import RelativeValuationService
from app.services.fcfe_ddm_engine import FCFEEngine, DividendDiscountEngine, PayoutPolicyDiagnosticService

def run_diagnostics(assumption_set: DcfAssumptionSet, output: DcfOutput, projection_years: list[DcfProjectionYear], terminal_fcff: float) -> list[dict[str, Any]]:
    return DiagnosticsEngine.run_all_diagnostics(assumption_set, output, projection_years, terminal_fcff)


def _calc_value_for_overrides(base_set: DcfAssumptionSet, overrides: dict[str, float]) -> float:
    # A lightweight runner for sensitivity that handles multiple overrides
    wacc_terminal = overrides.get("wacc_terminal", base_set.wacc_terminal or 0.10)
    wacc_start = overrides.get("wacc_start", base_set.wacc_start or 0.10)
    terminal_growth_rate = overrides.get("terminal_growth_rate", base_set.terminal_growth_rate or 0.02)
    terminal_roic = overrides.get("terminal_roic", base_set.terminal_roic or wacc_terminal)

    target_operating_margin = overrides.get("target_operating_margin", base_set.target_operating_margin or (base_set.current_operating_margin or 0.0))
    current_operating_margin = base_set.current_operating_margin or 0.0
    tax_rate = base_set.tax_rate or 0.21
    sales_to_capital_ratio = overrides.get("sales_to_capital_ratio", base_set.sales_to_capital_ratio or 1.0)
    revenue_growth_modifier = overrides.get("revenue_growth_modifier", 0.0)

    # WACC recalculation if cost of equity / debt overrides are provided
    if any(k in overrides for k in ["beta", "equity_risk_premium", "cost_of_equity", "debt_to_capital", "pre_tax_cost_of_debt"]):
        beta = overrides.get("beta", base_set.beta or 1.0)
        erp = overrides.get("equity_risk_premium", base_set.equity_risk_premium or 0.05)
        rfr = base_set.risk_free_rate or 0.04

        coe = overrides.get("cost_of_equity", rfr + beta * erp)
        dtc = overrides.get("debt_to_capital", base_set.debt_to_capital or 0.0)
        etc = 1.0 - dtc
        cod = overrides.get("pre_tax_cost_of_debt", base_set.pre_tax_cost_of_debt or 0.05)

        calculated_wacc = coe * etc + cod * (1 - tax_rate) * dtc
        wacc_start = calculated_wacc
        wacc_terminal = calculated_wacc
        terminal_roic = overrides.get("terminal_roic", calculated_wacc) # Default TROIC to WACC if not overridden

    # Recalculate discount factors and TV
    sum_pv_fcff = 0.0
    cumulative_discount_factor = 1.0
    last_revenue = base_set.starting_revenue or 0.0

    revenue_growth_years = base_set.revenue_growth_years_json or {}
    projection_years_count = base_set.projection_years_count or 10

    for year in range(1, projection_years_count + 1):
        growth_rate_str = str(year)
        base_growth = float(revenue_growth_years.get(growth_rate_str, 0.0))
        growth_rate = base_growth + revenue_growth_modifier

        revenue = last_revenue * (1 + growth_rate)
        margin_delta = target_operating_margin - current_operating_margin
        ebit_margin = current_operating_margin + (margin_delta * (year / projection_years_count))
        ebit = revenue * ebit_margin
        nopat = ebit * (1 - tax_rate)
        revenue_change = revenue - last_revenue
        reinvestment = (revenue_change / sales_to_capital_ratio) if sales_to_capital_ratio > 0 else 0.0
        fcff = nopat - reinvestment

        if year > (projection_years_count / 2):
            wacc_delta = wacc_terminal - wacc_start
            fade_years = projection_years_count - (projection_years_count / 2)
            wacc = wacc_start + wacc_delta * ((year - (projection_years_count / 2)) / fade_years)
        else:
            wacc = wacc_start

        cumulative_discount_factor *= (1 + wacc)
        sum_pv_fcff += fcff / cumulative_discount_factor
        last_revenue = revenue

    terminal_reinvestment_rate = (terminal_growth_rate / terminal_roic) if terminal_roic > 0 else 0.0
    terminal_revenue = last_revenue * (1 + terminal_growth_rate)
    terminal_ebit = terminal_revenue * target_operating_margin
    terminal_nopat = terminal_ebit * (1 - tax_rate)
    terminal_fcff = terminal_nopat * (1 - terminal_reinvestment_rate)

    if wacc_terminal > terminal_growth_rate:
        terminal_value = terminal_fcff / (wacc_terminal - terminal_growth_rate)
    else:
        terminal_value = 0.0

    pv_terminal_value = terminal_value / cumulative_discount_factor
    enterprise_value = sum_pv_fcff + pv_terminal_value

    cash = base_set.cash or 0.0
    debt = base_set.debt or 0.0
    minority_interests = base_set.minority_interests or 0.0
    preferred_stock = base_set.preferred_stock or 0.0
    employee_options_value = base_set.employee_options_value or 0.0
    cross_holdings = base_set.cross_holdings or 0.0
    operating_leases = base_set.operating_leases or 0.0
    diluted_shares = base_set.diluted_shares or 1.0

    # Bridge to Equity
    equity_value = enterprise_value + cash + cross_holdings - debt - operating_leases - minority_interests - preferred_stock - employee_options_value
    return equity_value / diluted_shares if diluted_shares > 0 else 0.0


def _build_table(assumption_set: DcfAssumptionSet, table_type: str, x_name: str, x_key: str, x_steps: list[float], y_name: str, y_key: str, y_steps: list[float]) -> DcfSensitivityTable:
    values = {}
    for y_val in y_steps:
        y_str = str(round(y_val, 4))
        values[y_str] = {}
        for x_val in x_steps:
            x_str = str(round(x_val, 4))
            overrides = {x_key: x_val, y_key: y_val}
            values[y_str][x_str] = _calc_value_for_overrides(assumption_set, overrides)

    return DcfSensitivityTable(
        assumption_set_id=assumption_set.id,
        table_type=table_type,
        x_axis_json={"name": x_name, "values": x_steps},
        y_axis_json={"name": y_name, "values": y_steps},
        values_json=values
    )


def generate_sensitivity_tables(assumption_set: DcfAssumptionSet) -> list[DcfSensitivityTable]:
    tables = []

    # 1. WACC vs Terminal Growth
    base_wacc = assumption_set.wacc_terminal or 0.10
    base_tg = assumption_set.terminal_growth_rate or 0.02
    wacc_steps = [base_wacc - 0.02, base_wacc - 0.01, base_wacc, base_wacc + 0.01, base_wacc + 0.02]
    tg_steps = [base_tg - 0.01, base_tg - 0.005, base_tg, base_tg + 0.005, base_tg + 0.01]
    tables.append(_build_table(assumption_set, "wacc_vs_terminal_growth", "Terminal Growth", "terminal_growth_rate", tg_steps, "WACC", "wacc_terminal", wacc_steps))

    # 2. Revenue Growth vs Target Margin
    base_margin = assumption_set.target_operating_margin or (assumption_set.current_operating_margin or 0.10)
    margin_steps = [base_margin - 0.04, base_margin - 0.02, base_margin, base_margin + 0.02, base_margin + 0.04]
    rg_steps = [-0.04, -0.02, 0.0, 0.02, 0.04] # Modifiers to base growth rates
    tables.append(_build_table(assumption_set, "revenue_growth_vs_target_margin", "Revenue Growth Offset", "revenue_growth_modifier", rg_steps, "Target Margin", "target_operating_margin", margin_steps))

    # 3. Sales-to-Capital vs Margin
    base_stc = assumption_set.sales_to_capital_ratio or 1.0
    stc_steps = [max(0.1, base_stc - 0.5), max(0.1, base_stc - 0.25), base_stc, base_stc + 0.25, base_stc + 0.5]
    tables.append(_build_table(assumption_set, "sales_to_capital_vs_margin", "Sales-to-Capital Ratio", "sales_to_capital_ratio", stc_steps, "Target Margin", "target_operating_margin", margin_steps))

    # 4. Terminal ROC vs Terminal Growth
    base_troic = assumption_set.terminal_roic or base_wacc
    troic_steps = [max(0.01, base_troic - 0.04), max(0.01, base_troic - 0.02), base_troic, base_troic + 0.02, base_troic + 0.04]
    tables.append(_build_table(assumption_set, "terminal_roc_vs_terminal_growth", "Terminal Growth", "terminal_growth_rate", tg_steps, "Terminal ROIC", "terminal_roic", troic_steps))

    # 5. Beta vs Equity Risk Premium
    base_beta = assumption_set.beta or 1.0
    base_erp = assumption_set.equity_risk_premium or 0.05
    beta_steps = [max(0.1, base_beta - 0.4), max(0.1, base_beta - 0.2), base_beta, base_beta + 0.2, base_beta + 0.4]
    erp_steps = [max(0.01, base_erp - 0.02), max(0.01, base_erp - 0.01), base_erp, base_erp + 0.01, base_erp + 0.02]
    tables.append(_build_table(assumption_set, "beta_vs_equity_risk_premium", "Equity Risk Premium", "equity_risk_premium", erp_steps, "Beta", "beta", beta_steps))

    # 6. Debt Ratio vs Pre-Tax Cost of Debt
    base_dtc = assumption_set.debt_to_capital or 0.0
    base_cod = assumption_set.pre_tax_cost_of_debt or 0.05
    dtc_steps = [max(0.0, base_dtc - 0.2), max(0.0, base_dtc - 0.1), base_dtc, min(1.0, base_dtc + 0.1), min(1.0, base_dtc + 0.2)]
    cod_steps = [max(0.01, base_cod - 0.02), max(0.01, base_cod - 0.01), base_cod, base_cod + 0.01, base_cod + 0.02]
    tables.append(_build_table(assumption_set, "debt_ratio_vs_cost_of_debt", "Pre-Tax Cost of Debt", "pre_tax_cost_of_debt", cod_steps, "Debt to Capital", "debt_to_capital", dtc_steps))

    return tables


def calculate_dcf(assumption_set: DcfAssumptionSet, model_type: str = "fcff_dcf") -> tuple[DcfOutput, list[DcfProjectionYear], list[DcfSensitivityTable]]:
    if model_type == "financial_services":
        return FinancialServicesEngine.calculate_excess_return_value(assumption_set)

    projection_years, sum_pv_fcff, last_revenue, cumulative_discount_factor = build_fcff_forecast(assumption_set)
    terminal_value, pv_terminal_value, terminal_fcff = calculate_terminal_value(assumption_set, last_revenue, cumulative_discount_factor)
    enterprise_value = sum_pv_fcff + pv_terminal_value

    equity_value, intrinsic_value_per_share, upside_downside_pct = calculate_equity_bridge(assumption_set, enterprise_value)

    terminal_value_pct_of_ev = (pv_terminal_value / enterprise_value) if enterprise_value != 0 else 0.0

    output = DcfOutput(
        assumption_set_id=assumption_set.id,
        sum_pv_fcff=sum_pv_fcff,
        terminal_value=terminal_value,
        pv_terminal_value=pv_terminal_value,
        enterprise_value=enterprise_value,
        cash=assumption_set.cash or 0.0,
        non_operating_assets=0.0,
        debt=assumption_set.debt or 0.0,
        cross_holdings=assumption_set.cross_holdings or 0.0,
        operating_leases=assumption_set.operating_leases or 0.0,
        minority_interests=assumption_set.minority_interests or 0.0,
        preferred_stock=assumption_set.preferred_stock or 0.0,
        employee_options_value=assumption_set.employee_options_value or 0.0,
        equity_value=equity_value,
        diluted_shares=assumption_set.diluted_shares or 1.0,
        intrinsic_value_per_share=intrinsic_value_per_share,
        current_market_price=assumption_set.current_market_price or 0.0,
        upside_downside_pct=upside_downside_pct,
        terminal_value_pct_of_ev=terminal_value_pct_of_ev
    )

    # Run Phase 11 Engines
    fcfe = FCFEEngine.calculate_fcfe(assumption_set)
    if fcfe is not None:
        output.fcfe_intrinsic_value_per_share = FCFEEngine.calculate_fcfe_intrinsic_value(assumption_set, fcfe)

    output.ddm_intrinsic_value_per_share = DividendDiscountEngine.calculate_ddm_intrinsic_value(assumption_set)

    warnings = run_diagnostics(assumption_set, output, projection_years, terminal_fcff)

    # Calculate implied multiples
    RelativeValuationService.calculate_implied_multiples(output, assumption_set)

    # Add relative pricing diagnostics
    relative_warnings = RelativeValuationService.generate_relative_pricing_diagnostics(output)
    warnings.extend([w.model_dump() for w in relative_warnings])

    # Apply Distressed Company logic if selected
    if model_type == "distressed":
        output = DistressedCompanyEngine.calculate_distressed_value(assumption_set, output)

    # Add payout diagnostics
    payout_warnings = PayoutPolicyDiagnosticService.run_diagnostics(assumption_set, fcfe, output)
    warnings.extend([w.model_dump() for w in payout_warnings])

    output.warnings_json = warnings

    sensitivity_tables = generate_sensitivity_tables(assumption_set)

    return output, projection_years, sensitivity_tables
