from math import isfinite

from app.models.dcf import DcfAssumptionSet, DcfOutput, DcfProjectionYear, DcfSensitivityTable
from app.services.financial_services_engine import FinancialServicesEngine
from app.services.distressed_engine import DistressedCompanyEngine


def _if_missing[T](value: T | None, default: T) -> T:
    """Retain explicit zeros; legacy presets apply only to absent inputs."""
    return default if value is None else value


def _projection_count(assumption_set: DcfAssumptionSet) -> int:
    count = _if_missing(assumption_set.projection_years_count, 10)
    if not 1 <= count <= 30:
        raise ValueError("projection_years_count must be between 1 and 30")
    return count

def build_fcff_forecast(assumption_set: DcfAssumptionSet) -> tuple[list[DcfProjectionYear], float, float, float]:
    starting_revenue = assumption_set.starting_revenue or 0.0
    current_operating_margin = assumption_set.current_operating_margin or 0.0
    target_operating_margin = _if_missing(assumption_set.target_operating_margin, current_operating_margin)
    tax_rate = _if_missing(assumption_set.tax_rate, 0.21)
    sales_to_capital_ratio = _if_missing(assumption_set.sales_to_capital_ratio, 1.0)
    starting_invested_capital = assumption_set.starting_invested_capital or 0.0
    revenue_growth_years = assumption_set.revenue_growth_years_json or {}
    wacc_start = _if_missing(assumption_set.wacc_start, 0.10)
    wacc_terminal = _if_missing(assumption_set.wacc_terminal, wacc_start)
    projection_years_count = _projection_count(assumption_set)

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
            calendar_year=None,  # No reviewed fiscal-year anchor is stored.
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
    target_operating_margin = _if_missing(assumption_set.target_operating_margin, assumption_set.current_operating_margin or 0.0)
    tax_rate = _if_missing(assumption_set.tax_rate, 0.21)
    terminal_growth_rate = _if_missing(assumption_set.terminal_growth_rate, 0.02)
    wacc_terminal = _if_missing(assumption_set.wacc_terminal, 0.10)
    terminal_roic = _if_missing(assumption_set.terminal_roic, wacc_terminal)

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


def calculate_equity_bridge(assumption_set: DcfAssumptionSet, enterprise_value: float) -> tuple[float, float, float | None]:
    cash = assumption_set.cash or 0.0
    debt = assumption_set.debt or 0.0
    minority_interests = assumption_set.minority_interests or 0.0
    preferred_stock = assumption_set.preferred_stock or 0.0
    employee_options_value = assumption_set.employee_options_value or 0.0
    cross_holdings = assumption_set.cross_holdings or 0.0
    operating_leases = assumption_set.operating_leases or 0.0
    diluted_shares = _if_missing(assumption_set.diluted_shares, 1.0)
    current_market_price = assumption_set.current_market_price or 0.0

    equity_value = enterprise_value + cash + cross_holdings - debt - operating_leases - minority_interests - preferred_stock - employee_options_value
    intrinsic_value_per_share = equity_value / diluted_shares if diluted_shares > 0 else 0.0
    upside_downside_pct = (intrinsic_value_per_share / current_market_price - 1) if current_market_price > 0 else None
    if not isfinite(current_market_price) or (upside_downside_pct is not None and not isfinite(upside_downside_pct)):
        upside_downside_pct = None

    return equity_value, intrinsic_value_per_share, upside_downside_pct


from typing import Any
from app.services.diagnostics_engine import DiagnosticsEngine
from app.services.relative_valuation_service import RelativeValuationService
from app.services.fcfe_ddm_engine import FCFEEngine, DividendDiscountEngine, PayoutPolicyDiagnosticService

def run_diagnostics(assumption_set: DcfAssumptionSet, output: DcfOutput, projection_years: list[DcfProjectionYear], terminal_fcff: float) -> list[dict[str, Any]]:
    return DiagnosticsEngine.run_all_diagnostics(assumption_set, output, projection_years, terminal_fcff)


class _SensitivityUnavailable(ValueError):
    """Stable per-cell diagnostic, safe to retain in saved sensitivity JSON."""


def _missing_funding_inputs(assumptions, overrides) -> list[str]:
    needed = {"debt_to_capital", "pre_tax_cost_of_debt", "tax_rate"}
    if assumptions.cost_of_equity is None:
        needed |= {"risk_free_rate", "beta", "equity_risk_premium"}
    if {"beta", "equity_risk_premium"}.intersection(overrides):
        needed |= {"beta", "equity_risk_premium"}
    return sorted(key for key in needed if getattr(assumptions, key) is None)


def _calc_value_for_overrides(base_set: DcfAssumptionSet, overrides: dict[str, float]) -> float:
    # Clone scalar inputs only; never mutate a saved ORM object or its relations.
    from copy import deepcopy
    from math import isfinite
    from types import SimpleNamespace

    row = SimpleNamespace(**{c.key: deepcopy(getattr(base_set, c.key)) for c in DcfAssumptionSet.__table__.columns})
    if row.is_stale:
        raise _SensitivityUnavailable("STALE_INPUT: review and save a new basis.")
    for field in ("starting_revenue", "wacc_start", "wacc_terminal", "diluted_shares", "sales_to_capital_ratio"):
        if getattr(row, field) is None:
            raise _SensitivityUnavailable(f"MISSING_INPUT: explicit {field} is required.")
    for column in DcfAssumptionSet.__table__.columns:
        value = getattr(row, column.key)
        if isinstance(value, float) and not isfinite(value):
            raise _SensitivityUnavailable("NONFINITE_INPUT: all numeric inputs must be finite.")
    try:
        count = _projection_count(row)
        if type(count) is not int:
            raise ValueError
    except ValueError:
        raise _SensitivityUnavailable("PROJECTION_COUNT: projection_years_count must be 1-30.") from None
    allowed = {"wacc_start", "wacc_terminal", "terminal_growth_rate", "terminal_roic",
        "target_operating_margin", "sales_to_capital_ratio", "revenue_growth_modifier",
        "beta", "equity_risk_premium", "cost_of_equity", "debt_to_capital", "pre_tax_cost_of_debt"}
    if any(key not in allowed or isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value)
           for key, value in overrides.items()):
        raise _SensitivityUnavailable("INVALID_OVERRIDE: unsupported or nonfinite sensitivity input.")
    # Resolve missing terminal ROIC before any rate shock; it never follows shocked WACC.
    row.terminal_roic = _if_missing(base_set.terminal_roic, base_set.wacc_terminal)
    funding = {"beta", "equity_risk_premium", "cost_of_equity", "debt_to_capital", "pre_tax_cost_of_debt"}
    if funding.intersection(overrides):
        missing = _missing_funding_inputs(base_set, overrides)
        if missing:
            raise _SensitivityUnavailable("MISSING_FUNDING_INPUT: explicit " + ", ".join(missing) + " required; saved discount rates remain usable.")
        beta, erp = base_set.beta, base_set.equity_risk_premium
        coe = base_set.cost_of_equity if base_set.cost_of_equity is not None else base_set.risk_free_rate + beta * erp
        debt = base_set.debt_to_capital
        cod, tax = base_set.pre_tax_cost_of_debt, base_set.tax_rate
        shocked_coe = overrides.get("cost_of_equity", coe)
        if {"beta", "equity_risk_premium"}.intersection(overrides) and "cost_of_equity" not in overrides:
            shocked_coe = coe + overrides.get("beta", beta) * overrides.get("equity_risk_premium", erp) - beta * erp
        shocked_debt = overrides.get("debt_to_capital", debt)
        shocked_cod = overrides.get("pre_tax_cost_of_debt", cod)
        if (not 0 <= shocked_debt <= 1 or not 0 <= shocked_cod <= 1 or not 0 <= shocked_coe <= 1
            or (beta is not None and not 0 <= overrides.get("beta", beta) <= 5)
            or (erp is not None and not 0 <= overrides.get("equity_risk_premium", erp) <= 1)):
            raise _SensitivityUnavailable("FUNDING_RANGE: funding weights and rates are invalid.")
        before = coe * (1 - debt) + cod * (1 - tax) * debt
        after = shocked_coe * (1 - shocked_debt) + shocked_cod * (1 - tax) * shocked_debt
        # Preserve the saved WACC level/fade, including a saved non-CAPM equity cost.
        row.wacc_start += after - before
        row.wacc_terminal += after - before
    for key, value in overrides.items():
        if key not in funding and key != "revenue_growth_modifier":
            setattr(row, key, value)
    try:
        row.revenue_growth_years_json = {
            str(year): float((base_set.revenue_growth_years_json or {}).get(str(year), 0)) + overrides.get("revenue_growth_modifier", 0)
            for year in range(1, count + 1)
        }
    except (TypeError, ValueError, AttributeError):
        raise _SensitivityUnavailable("GROWTH_RANGE: invalid annual growth inputs.") from None
    if any(not isfinite(value) or value < -1 for value in row.revenue_growth_years_json.values()):
        raise _SensitivityUnavailable("GROWTH_RANGE: growth must be finite and at least -100%.")
    growth = _if_missing(row.terminal_growth_rate, .02)
    if row.wacc_terminal - growth <= 1e-6:
        raise _SensitivityUnavailable("TERMINAL_CONVERGENCE: terminal WACC must exceed growth by more than 0.0001 percentage points.")
    if not 0 <= row.wacc_start <= 1 or not 0 <= row.wacc_terminal <= 1:
        raise _SensitivityUnavailable("DISCOUNT_RATE: WACC must be between zero and one.")
    if row.sales_to_capital_ratio <= 0:
        raise _SensitivityUnavailable("SALES_TO_CAPITAL: a positive reinvestment ratio is required.")
    if row.diluted_shares <= 0:
        raise _SensitivityUnavailable("DILUTED_SHARES: positive explicit diluted shares are required.")
    if row.terminal_roic <= 0:
        raise _SensitivityUnavailable("TERMINAL_ROIC: a positive terminal return on capital is required.")
    if row.starting_revenue <= 0 or not 0 <= _if_missing(row.tax_rate, .21) <= 1 or not -1 <= _if_missing(row.target_operating_margin, row.current_operating_margin or 0) <= 1:
        raise _SensitivityUnavailable("INPUT_RANGE: review revenue, tax and margin assumptions.")
    if row.cash_flow_currency and row.discount_rate_currency and row.cash_flow_currency != row.discount_rate_currency and not (row.currency_override_note or "").strip():
        raise _SensitivityUnavailable("CURRENCY_MISMATCH: review the currency basis before calculation.")
    _, forecast_pv, revenue, factor = build_fcff_forecast(row)
    _, terminal_pv, _ = calculate_terminal_value(row, revenue, factor)
    _, per_share, _ = calculate_equity_bridge(row, forecast_pv + terminal_pv)
    if not isfinite(per_share):
        raise _SensitivityUnavailable("NONFINITE_RESULT: this cell cannot be represented.")
    return per_share


def _build_table(assumption_set: DcfAssumptionSet, table_type: str, x_name: str, x_key: str, x_steps: list[float], y_name: str, y_key: str, y_steps: list[float]) -> DcfSensitivityTable:
    import hashlib
    import json

    values = {}
    errors = {}
    funding_axes = {"beta", "equity_risk_premium", "cost_of_equity", "debt_to_capital", "pre_tax_cost_of_debt"}
    missing = _missing_funding_inputs(assumption_set, {x_key, y_key}) if funding_axes.intersection({x_key, y_key}) else []
    unavailable_reason = None
    if missing:
        unavailable_reason = "MISSING_FUNDING_INPUT: explicit " + ", ".join(missing) + " required; no funding sensitivity is calculated."
        x_steps, y_steps = [], []
    for y_val in y_steps:
        y_str = str(round(y_val, 4))
        values[y_str] = {}
        errors[y_str] = {}
        for x_val in x_steps:
            x_str = str(round(x_val, 4))
            overrides = {x_key: x_val, y_key: y_val}
            try:
                values[y_str][x_str] = _calc_value_for_overrides(assumption_set, overrides)
            except _SensitivityUnavailable as exc:
                values[y_str][x_str] = None
                errors[y_str][x_str] = str(exc)
            except (OverflowError, ZeroDivisionError):
                values[y_str][x_str] = None
                errors[y_str][x_str] = "NONFINITE_RESULT: the calculation exceeded its numeric range."

    basis = {column.key: getattr(assumption_set, column.key) for column in DcfAssumptionSet.__table__.columns}
    method = {"version": "fcff-sensitivity-v2", "assumption_set_id": assumption_set.id,
        "input_sha256": hashlib.sha256(json.dumps(basis, sort_keys=True, default=str).encode()).hexdigest(),
        "currency": assumption_set.cash_flow_currency, "claim_type": "Calculation",
        "funding": "Changes in weighted funding cost shift both saved WACCs equally; saved equity-cost residual and terminal ROIC are retained.",
        "basis": "Saved assumptions with canonical FCFF forecast, terminal value and equity bridge. Not a probability distribution.",
        "funding_input_policy": "explicit_required_v1",
        "defaulted_fields": [key for key in ("tax_rate", "target_operating_margin", "terminal_growth_rate", "terminal_roic") if getattr(assumption_set, key) is None]}

    return DcfSensitivityTable(
        assumption_set_id=assumption_set.id,
        table_type=table_type,
        x_axis_json={"name": x_name, "values": x_steps, "method": method, "cell_errors": errors,
                     **({"unavailable_reason": unavailable_reason} if unavailable_reason else {})},
        y_axis_json={"name": y_name, "values": y_steps},
        values_json=values
    )


def generate_sensitivity_tables(assumption_set: DcfAssumptionSet) -> list[DcfSensitivityTable]:
    tables = []

    # 1. WACC vs Terminal Growth
    base_wacc = _if_missing(assumption_set.wacc_terminal, 0.10)
    base_tg = _if_missing(assumption_set.terminal_growth_rate, 0.02)
    wacc_steps = [base_wacc - 0.02, base_wacc - 0.01, base_wacc, base_wacc + 0.01, base_wacc + 0.02]
    tg_steps = [base_tg - 0.01, base_tg - 0.005, base_tg, base_tg + 0.005, base_tg + 0.01]
    tables.append(_build_table(assumption_set, "wacc_vs_terminal_growth", "Terminal Growth", "terminal_growth_rate", tg_steps, "WACC", "wacc_terminal", wacc_steps))

    # 2. Revenue Growth vs Target Margin
    base_margin = _if_missing(assumption_set.target_operating_margin, _if_missing(assumption_set.current_operating_margin, 0.0))
    margin_steps = [base_margin - 0.04, base_margin - 0.02, base_margin, base_margin + 0.02, base_margin + 0.04]
    rg_steps = [-0.04, -0.02, 0.0, 0.02, 0.04] # Modifiers to base growth rates
    tables.append(_build_table(assumption_set, "revenue_growth_vs_target_margin", "Revenue Growth Offset", "revenue_growth_modifier", rg_steps, "Target Margin", "target_operating_margin", margin_steps))

    # 3. Sales-to-Capital vs Margin
    base_stc = _if_missing(assumption_set.sales_to_capital_ratio, 1.0)
    stc_steps = [base_stc - 0.5, base_stc - 0.25, base_stc, base_stc + 0.25, base_stc + 0.5]
    tables.append(_build_table(assumption_set, "sales_to_capital_vs_margin", "Sales-to-Capital Ratio", "sales_to_capital_ratio", stc_steps, "Target Margin", "target_operating_margin", margin_steps))

    # 4. Terminal ROC vs Terminal Growth
    base_troic = _if_missing(assumption_set.terminal_roic, base_wacc)
    troic_steps = [base_troic - 0.04, base_troic - 0.02, base_troic, base_troic + 0.02, base_troic + 0.04]
    tables.append(_build_table(assumption_set, "terminal_roc_vs_terminal_growth", "Terminal Growth", "terminal_growth_rate", tg_steps, "Terminal ROIC", "terminal_roic", troic_steps))

    # 5. Beta vs Equity Risk Premium
    base_beta = _if_missing(assumption_set.beta, 1.0)
    base_erp = _if_missing(assumption_set.equity_risk_premium, 0.05)
    beta_steps = [base_beta - 0.4, base_beta - 0.2, base_beta, base_beta + 0.2, base_beta + 0.4]
    erp_steps = [base_erp - 0.02, base_erp - 0.01, base_erp, base_erp + 0.01, base_erp + 0.02]
    tables.append(_build_table(assumption_set, "beta_vs_equity_risk_premium", "Equity Risk Premium", "equity_risk_premium", erp_steps, "Beta", "beta", beta_steps))

    # 6. Debt Ratio vs Pre-Tax Cost of Debt
    base_dtc = assumption_set.debt_to_capital or 0.0
    base_cod = _if_missing(assumption_set.pre_tax_cost_of_debt, 0.05)
    dtc_steps = [base_dtc - 0.2, base_dtc - 0.1, base_dtc, base_dtc + 0.1, base_dtc + 0.2]
    cod_steps = [base_cod - 0.02, base_cod - 0.01, base_cod, base_cod + 0.01, base_cod + 0.02]
    tables.append(_build_table(assumption_set, "debt_ratio_vs_cost_of_debt", "Pre-Tax Cost of Debt", "pre_tax_cost_of_debt", cod_steps, "Debt to Capital", "debt_to_capital", dtc_steps))

    return tables


def calculate_dcf(assumption_set: DcfAssumptionSet, model_type: str = "fcff_dcf", *, include_sensitivity: bool = True) -> tuple[DcfOutput, list[DcfProjectionYear], list[DcfSensitivityTable]]:
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
        diluted_shares=_if_missing(assumption_set.diluted_shares, 1.0),
        intrinsic_value_per_share=intrinsic_value_per_share,
        current_market_price=assumption_set.current_market_price if (assumption_set.current_market_price or 0) > 0 and isfinite(assumption_set.current_market_price) else None,
        upside_downside_pct=upside_downside_pct,
        terminal_value_pct_of_ev=terminal_value_pct_of_ev
    )

    # Run Phase 11 Engines
    fcfe = FCFEEngine.calculate_fcfe(assumption_set)
    if fcfe is not None:
        output.fcfe_intrinsic_value_per_share = FCFEEngine.calculate_fcfe_intrinsic_value(assumption_set, fcfe)

    output.ddm_intrinsic_value_per_share = DividendDiscountEngine.calculate_ddm_intrinsic_value(assumption_set)

    warnings = run_diagnostics(assumption_set, output, projection_years, terminal_fcff)

    # Apply Distressed Company logic if selected
    if model_type == "distressed":
        output = DistressedCompanyEngine.calculate_distressed_value(assumption_set, output)
        warnings.extend(output.warnings_json or [])

    # Add payout diagnostics
    payout_warnings = PayoutPolicyDiagnosticService.run_diagnostics(assumption_set, fcfe, output)
    warnings.extend([w.model_dump() for w in payout_warnings])

    # Ratios use the final DCF values and respect the completed trust diagnostics.
    output.warnings_json = warnings
    RelativeValuationService.calculate_implied_multiples(output, assumption_set)
    relative_warnings = RelativeValuationService.generate_relative_pricing_diagnostics(output)
    warnings.extend([w.model_dump() for w in relative_warnings])

    output.warnings_json = warnings
    output.model_quality_score = DiagnosticsEngine.quality_score(warnings)

    # FCFF sensitivities do not include probability-weighted equity recovery.
    sensitivity_tables = generate_sensitivity_tables(assumption_set) if include_sensitivity and model_type != "distressed" else []

    return output, projection_years, sensitivity_tables
