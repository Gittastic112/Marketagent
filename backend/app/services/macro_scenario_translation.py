from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.macro_sensitivity import SectorMacroSensitivityBenchmark
from app.services.macro_context import (
    DEFAULT_MACRO_COUNTRY,
    DEFAULT_MACRO_MARKET,
    NEGATIVE_DURATION_WARNING,
    benchmark_context,
)


class MacroScenarioTranslationService:
    @classmethod
    def translate(
        cls,
        db: Session,
        *,
        market: str = DEFAULT_MACRO_MARKET,
        country: str = DEFAULT_MACRO_COUNTRY,
        sic_code: str,
        rate_shock: float,
        gdp_shock: float,
        inflation_shock: float,
        currency_shock: float,
        currency_variable_direction: str | None = None,
    ) -> dict[str, Any]:
        benchmark = db.scalar(
            select(SectorMacroSensitivityBenchmark).where(
                SectorMacroSensitivityBenchmark.market == market,
                SectorMacroSensitivityBenchmark.country == country,
                SectorMacroSensitivityBenchmark.sic_code == sic_code
            )
        )
        if not benchmark:
            raise LookupError("Sector macro sensitivity benchmark not found")

        value_impact = cls._weighted_impact(
            benchmark.firm_value_duration,
            benchmark.firm_value_cyclicality,
            benchmark.firm_value_inflation,
            benchmark.firm_value_currency,
            rate_shock,
            gdp_shock,
            inflation_shock,
            currency_shock,
        )
        operating_income_impact = cls._weighted_impact(
            benchmark.operating_income_duration,
            benchmark.operating_income_cyclicality,
            benchmark.operating_income_inflation,
            benchmark.operating_income_currency,
            rate_shock,
            gdp_shock,
            inflation_shock,
            currency_shock,
        )

        warnings = [
            "This is a sector-level benchmark, not company-specific regression output.",
            "This scenario does not automatically change valuation assumptions.",
            (
                "Currency sensitivity is only meaningful if the currency series direction "
                "is clearly defined."
            ),
        ]
        if benchmark.firm_value_duration is not None and benchmark.firm_value_duration < 0:
            warnings.append(NEGATIVE_DURATION_WARNING)

        return {
            "method": "sector_macro_sensitivity",
            **benchmark_context(benchmark),
            "sic_code": benchmark.sic_code,
            "industry_name": benchmark.industry_name,
            "source_file": benchmark.source_file,
            "currency_variable_direction": currency_variable_direction,
            "estimated_value_impact_pct": round(value_impact, 10),
            "estimated_operating_income_impact_pct": round(operating_income_impact, 10),
            "affected_assumptions": cls._affected_assumptions(
                rate_shock,
                gdp_shock,
                inflation_shock,
                currency_shock,
            ),
            "warnings": warnings,
            "formula": (
                "estimated_impact = duration * rate_shock + cyclicality * gdp_shock "
                "+ inflation_sensitivity * inflation_shock + currency_sensitivity "
                f"* currency_shock; source_file={benchmark.source_file}"
            ),
            "confidence": "medium",
        }

    @staticmethod
    def _weighted_impact(
        duration: float | None,
        cyclicality: float | None,
        inflation: float | None,
        currency: float | None,
        rate_shock: float,
        gdp_shock: float,
        inflation_shock: float,
        currency_shock: float,
    ) -> float:
        return (
            (duration or 0.0) * rate_shock
            + (cyclicality or 0.0) * gdp_shock
            + (inflation or 0.0) * inflation_shock
            + (currency or 0.0) * currency_shock
        )

    @staticmethod
    def _affected_assumptions(
        rate_shock: float,
        gdp_shock: float,
        inflation_shock: float,
        currency_shock: float,
    ) -> list[str]:
        assumptions: list[str] = []
        if rate_shock:
            assumptions.extend(["risk_free_rate", "terminal_value"])
        if gdp_shock:
            assumptions.extend(["revenue_growth", "operating_margin"])
        if inflation_shock:
            assumptions.extend(["revenue_growth", "operating_margin"])
        if currency_shock:
            assumptions.append("currency_translation")

        return list(dict.fromkeys(assumptions))
