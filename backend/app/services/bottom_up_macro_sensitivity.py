from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.macro_sensitivity import SectorMacroSensitivityBenchmark
from app.services.macro_context import (
    DEFAULT_MACRO_COUNTRY,
    DEFAULT_MACRO_MARKET,
    NEGATIVE_DURATION_WARNING,
    duration_interpretation,
    duration_magnitude,
)


class BottomUpMacroSensitivityService:
    @classmethod
    def calculate(
        cls,
        db: Session,
        *,
        segments: list[dict[str, Any]],
        market: str = DEFAULT_MACRO_MARKET,
        country: str = DEFAULT_MACRO_COUNTRY,
    ) -> dict[str, Any]:
        total_value = sum(float(segment["value"]) for segment in segments)
        if total_value <= 0:
            raise ValueError("Total segment value must be greater than zero.")

        weighted = {
            "duration": 0.0,
            "cyclicality": 0.0,
            "inflation_sensitivity": 0.0,
            "currency_sensitivity": 0.0,
        }
        segment_exposures: list[dict[str, Any]] = []
        missing_segments: list[dict[str, Any]] = []
        covered_weight = 0.0

        for segment in segments:
            weight = float(segment["value"]) / total_value
            sic_code = str(segment["sic_code"])
            benchmark = db.scalar(
                select(SectorMacroSensitivityBenchmark).where(
                    SectorMacroSensitivityBenchmark.market == market,
                    SectorMacroSensitivityBenchmark.country == country,
                    SectorMacroSensitivityBenchmark.sic_code == sic_code
                )
            )
            if not benchmark:
                missing_segments.append(
                    {
                        "name": segment["name"],
                        "sic_code": sic_code,
                        "weight": round(weight, 10),
                    }
                )
                continue

            duration = benchmark.firm_value_duration or 0.0
            cyclicality = benchmark.firm_value_cyclicality or 0.0
            inflation = benchmark.firm_value_inflation or 0.0
            currency = benchmark.firm_value_currency or 0.0

            covered_weight += weight
            weighted["duration"] += weight * duration
            weighted["cyclicality"] += weight * cyclicality
            weighted["inflation_sensitivity"] += weight * inflation
            weighted["currency_sensitivity"] += weight * currency

            segment_exposures.append(
                {
                    "name": segment["name"],
                    "sic_code": sic_code,
                    "market": benchmark.market,
                    "country": benchmark.country,
                    "classification_system": benchmark.classification_system,
                    "currency_context": benchmark.currency_context,
                    "industry_name": benchmark.industry_name,
                    "weight": round(weight, 10),
                    "duration": duration,
                    "cyclicality": cyclicality,
                    "inflation_sensitivity": inflation,
                    "currency_sensitivity": currency,
                    "source_file": benchmark.source_file,
                }
            )

        if not segment_exposures:
            raise LookupError("No SIC macro sensitivity benchmarks found for submitted segments.")

        warnings = [
            "Bottom-up sensitivity uses sector-level benchmarks, not company-specific regression output.",
            "This output does not automatically change valuation assumptions.",
        ]
        if missing_segments:
            missing_codes = ", ".join(segment["sic_code"] for segment in missing_segments)
            warnings.append(f"Missing SIC benchmark coverage for: {missing_codes}.")
        if weighted["duration"] < 0:
            warnings.append(NEGATIVE_DURATION_WARNING)

        return {
            "method": "bottom_up",
            "market": market,
            "country": country,
            "duration": round(weighted["duration"], 10),
            "duration_magnitude": duration_magnitude(round(weighted["duration"], 10)),
            "duration_interpretation": duration_interpretation(weighted["duration"]),
            "cyclicality": round(weighted["cyclicality"], 10),
            "inflation_sensitivity": round(weighted["inflation_sensitivity"], 10),
            "currency_sensitivity": round(weighted["currency_sensitivity"], 10),
            "covered_weight": round(covered_weight, 10),
            "confidence": "medium" if covered_weight >= 0.95 else "low",
            "segment_exposures": segment_exposures,
            "missing_segments": missing_segments,
            "warnings": warnings,
            "formula": (
                "Company sensitivity = sum(segment_value / total_segment_value "
                "* sector_sensitivity). Missing SIC segments contribute zero and reduce coverage."
            ),
        }
