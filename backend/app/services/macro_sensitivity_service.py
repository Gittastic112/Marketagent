import statistics
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.macro_sensitivity import (
    CompanyMacroInput,
    CompanyMacroSensitivityResult,
    CompanyMacroSegmentExposure,
    SectorMacroSensitivityBenchmark
)
from app.schemas.macro import (
    MacroTopDownRequest,
    MacroBottomUpRequest,
    MacroSensitivityResult,
    MacroSensitivityMetrics
)

def _calculate_slope(x: List[float], y: List[float]) -> Optional[float]:
    if len(x) != len(y) or len(x) < 2:
        return None
    try:
        slope, intercept = statistics.linear_regression(x, y)
        return slope
    except Exception:
        return None

def run_top_down_macro_sensitivity(db: Session, request: MacroTopDownRequest) -> MacroSensitivityResult:
    """
    Run top-down regression of company history vs macro variables.
    Currently a mock/stub since macro time series are not yet fully ingested.
    """
    # 1. Save inputs to CompanyMacroInput
    for p in request.periods:
        # In a real implementation we would upsert or check for existence
        input_row = CompanyMacroInput(
            company_id=request.company_id,
            period_label=p.period_label,
            period_end_date=p.period_end_date,
            operating_income=p.operating_income,
            market_cap=p.market_cap,
            total_debt=p.total_debt,
            cash=p.cash,
            enterprise_value=p.enterprise_value
        )
        db.add(input_row)

    # 2. Fetch macro data and compute regression (Mocked for now)
    obs_count = len(request.periods)
    warnings = []
    confidence = "high"

    if obs_count < 8:
        confidence = "low"
        warnings.append("Regression output should be interpreted with caution because sample size is limited.")

    # Mocked slopes and results
    duration = 0.0
    cyclicality = 1.0
    inflation = 0.5
    currency = -0.2

    # In real logic:
    # duration = max(0, -1 * rate_slope)

    firm_metrics = MacroSensitivityMetrics(
        duration=duration,
        cyclicality=cyclicality,
        inflation_sensitivity=inflation,
        currency_sensitivity=currency
    )

    op_metrics = MacroSensitivityMetrics(
        duration=duration + 0.5,
        cyclicality=cyclicality - 0.2,
        inflation_sensitivity=inflation + 0.1,
        currency_sensitivity=currency + 0.1
    )

    result_row = CompanyMacroSensitivityResult(
        company_id=request.company_id,
        valuation_id=request.valuation_id,
        method="top_down",
        dependent_variable="both",
        observation_count=obs_count,
        duration=duration,
        cyclicality=cyclicality,
        inflation_sensitivity=inflation,
        currency_sensitivity=currency,
        confidence_label=confidence,
        warnings=warnings
    )
    db.add(result_row)
    db.commit()

    return MacroSensitivityResult(
        method="top_down",
        observation_count=obs_count,
        firm_value=firm_metrics,
        operating_income=op_metrics,
        confidence_label=confidence,
        warnings=warnings
    )


def run_bottom_up_macro_sensitivity(db: Session, request: MacroBottomUpRequest) -> MacroSensitivityResult:
    """
    Run bottom-up calculation of company macro sensitivity using segment weights.
    """
    total_weight = sum(s.segment_weight for s in request.segments if s.segment_weight is not None)

    if total_weight == 0:
        # Try to infer weights from values or revenue
        total_value = sum(s.segment_value or 0 for s in request.segments)
        if total_value > 0:
            for s in request.segments:
                s.segment_weight = (s.segment_value or 0) / total_value
        else:
            total_rev = sum(s.segment_revenue or 0 for s in request.segments)
            if total_rev > 0:
                for s in request.segments:
                    s.segment_weight = (s.segment_revenue or 0) / total_rev

    warnings = []

    firm_dur = 0.0
    firm_cyc = 0.0
    firm_inf = 0.0
    firm_cur = 0.0

    for seg in request.segments:
        # Fetch benchmark for this segment (by SIC or name)
        stmt = select(SectorMacroSensitivityBenchmark)
        if seg.sic_code:
            stmt = stmt.where(SectorMacroSensitivityBenchmark.sic_code == seg.sic_code)
        elif seg.benchmark_industry_name:
            stmt = stmt.where(SectorMacroSensitivityBenchmark.industry_name == seg.benchmark_industry_name)

        benchmark = db.execute(stmt).scalars().first()
        weight = seg.segment_weight or 0.0

        b_dur = benchmark.firm_value_duration if benchmark else 1.0
        b_cyc = benchmark.firm_value_cyclicality if benchmark else 1.0
        b_inf = benchmark.firm_value_inflation if benchmark else 0.5
        b_cur = benchmark.firm_value_currency if benchmark else 0.0

        firm_dur += weight * (b_dur or 0)
        firm_cyc += weight * (b_cyc or 0)
        firm_inf += weight * (b_inf or 0)
        firm_cur += weight * (b_cur or 0)

        exposure_row = CompanyMacroSegmentExposure(
            company_id=request.company_id,
            valuation_id=request.valuation_id,
            segment_name=seg.segment_name,
            sic_code=seg.sic_code,
            benchmark_industry_name=seg.benchmark_industry_name,
            segment_value=seg.segment_value,
            segment_revenue=seg.segment_revenue,
            segment_weight=weight,
            duration=b_dur,
            cyclicality=b_cyc,
            inflation_sensitivity=b_inf,
            currency_sensitivity=b_cur
        )
        db.add(exposure_row)

    if not any(s.sic_code for s in request.segments):
        warnings.append("Some segments had no SIC code mapped, falling back to neutral assumptions.")

    result_row = CompanyMacroSensitivityResult(
        company_id=request.company_id,
        valuation_id=request.valuation_id,
        method="bottom_up",
        dependent_variable="firm_value",
        duration=firm_dur,
        cyclicality=firm_cyc,
        inflation_sensitivity=firm_inf,
        currency_sensitivity=firm_cur,
        confidence_label="high",
        warnings=warnings
    )
    db.add(result_row)
    db.commit()

    firm_metrics = MacroSensitivityMetrics(
        duration=firm_dur,
        cyclicality=firm_cyc,
        inflation_sensitivity=firm_inf,
        currency_sensitivity=firm_cur
    )

    return MacroSensitivityResult(
        method="bottom_up",
        observation_count=len(request.segments),
        firm_value=firm_metrics,
        operating_income=firm_metrics, # Mocked equality for bottom-up
        confidence_label="high",
        warnings=warnings
    )
