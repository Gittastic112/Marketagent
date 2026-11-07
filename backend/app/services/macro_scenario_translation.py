"""Non-writing shocks with separate covered contributions and unknown totals."""
import math
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.macro_sensitivity import SectorMacroSensitivityBenchmark
from app.services.macro_context import (
    DEFAULT_MACRO_COUNTRY, DEFAULT_MACRO_MARKET, NEGATIVE_DURATION_WARNING, benchmark_context,
)


class MacroScenarioTranslationService:
    @classmethod
    def translate(cls, db: Session, *, market: str = DEFAULT_MACRO_MARKET, country: str = DEFAULT_MACRO_COUNTRY,
                  sic_code: str, rate_shock: float, gdp_shock: float, inflation_shock: float,
                  currency_shock: float, currency_variable_direction: str | None = None) -> dict[str, Any]:
        shocks = dict(rate_shock=rate_shock, gdp_shock=gdp_shock, inflation_shock=inflation_shock, currency_shock=currency_shock)
        if not all(math.isfinite(value) for value in shocks.values()):
            raise ValueError("Shocks must be finite.")
        rows = list(db.scalars(select(SectorMacroSensitivityBenchmark).where(
            SectorMacroSensitivityBenchmark.market == market,
            SectorMacroSensitivityBenchmark.country == country,
            SectorMacroSensitivityBenchmark.sic_code == sic_code)))
        if not rows:
            raise LookupError("Sector macro sensitivity benchmark not found")
        if len(rows) != 1:
            raise ValueError("Ambiguous sector benchmark.")
        benchmark = rows[0]
        direction = (currency_variable_direction or "").strip() or None
        value, covered_value, missing_value = cls._weighted_impact(
            [benchmark.firm_value_duration, benchmark.firm_value_cyclicality,
             benchmark.firm_value_inflation, benchmark.firm_value_currency], shocks, direction)
        income, covered_income, missing_income = cls._weighted_impact(
            [benchmark.operating_income_duration, benchmark.operating_income_cyclicality,
             benchmark.operating_income_inflation, benchmark.operating_income_currency], shocks, direction)
        warnings = [
            "This is a sector-level benchmark, not company-specific regression output.",
            "This scenario does not automatically change valuation assumptions.",
            "Currency sensitivity requires an explicit direction consistent with the source series; a supplied direction is a User Assumption.",
        ]
        if missing_value or missing_income:
            warnings.append("Missing active coefficients or currency direction withhold the total impact; covered contributions are not a complete scenario.")
        if benchmark.firm_value_duration is not None and benchmark.firm_value_duration < 0:
            warnings.append(NEGATIVE_DURATION_WARNING)
        return {
            "method": "sector_macro_sensitivity", **benchmark_context(benchmark),
            "sic_code": benchmark.sic_code, "industry_name": benchmark.industry_name,
            "source_file": benchmark.source_file, "source_record_id": benchmark.id,
            "recorded_at": benchmark.created_at.isoformat() if benchmark.created_at else None,
            "currency_variable_direction": direction, "estimated_value_impact_pct": value,
            "estimated_operating_income_impact_pct": income, "covered_value_impact_pct": covered_value,
            "covered_operating_income_impact_pct": covered_income, "missing_value_factors": missing_value,
            "missing_operating_income_factors": missing_income, "shocks": shocks,
            "affected_assumptions": cls._affected_assumptions(rate_shock, gdp_shock, inflation_shock, currency_shock),
            "warnings": warnings, "claim_type": "Calculation",
            "formula": "estimated_impact = duration * rate_shock + cyclicality * gdp_shock + inflation_sensitivity * inflation_shock + currency_sensitivity * currency_shock; source_file=" + benchmark.source_file,
            "confidence": "low" if missing_value or missing_income else "medium",
        }

    @staticmethod
    def _weighted_impact(coefficients: list[float | None], shocks: dict[str, float], direction: str | None):
        missing, covered = [], 0.0
        for (factor, shock), coefficient in zip(shocks.items(), coefficients):
            if shock == 0:
                continue
            if coefficient is None or not math.isfinite(coefficient) or (factor == "currency_shock" and not direction):
                missing.append(factor)
                continue
            covered += coefficient * shock
        if not math.isfinite(covered):
            raise ValueError("Scenario impact exceeds the supported finite range.")
        return (None if missing else round(covered, 10), round(covered, 10), missing)

    @staticmethod
    def _affected_assumptions(rate_shock: float, gdp_shock: float, inflation_shock: float, currency_shock: float) -> list[str]:
        assumptions = []
        if rate_shock:
            assumptions.extend(["risk_free_rate", "terminal_value"])
        if gdp_shock or inflation_shock:
            assumptions.extend(["revenue_growth", "operating_margin"])
        if currency_shock:
            assumptions.append("currency_translation")
        return list(dict.fromkeys(assumptions))
