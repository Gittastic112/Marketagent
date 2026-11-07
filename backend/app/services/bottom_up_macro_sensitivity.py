"""Value-weighted sector sensitivity with explicit per-coefficient coverage."""
import math
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.macro_sensitivity import SectorMacroSensitivityBenchmark
from app.services.macro_context import (
    DEFAULT_MACRO_COUNTRY, DEFAULT_MACRO_MARKET, NEGATIVE_DURATION_WARNING,
    duration_interpretation, duration_magnitude,
)

COEFFICIENTS = {
    "duration": "firm_value_duration", "cyclicality": "firm_value_cyclicality",
    "inflation_sensitivity": "firm_value_inflation", "currency_sensitivity": "firm_value_currency",
}


class BottomUpMacroSensitivityService:
    @classmethod
    def calculate(cls, db: Session, *, segments: list[dict[str, Any]],
                  market: str = DEFAULT_MACRO_MARKET, country: str = DEFAULT_MACRO_COUNTRY) -> dict[str, Any]:
        if not 1 <= len(segments) <= 100:
            raise ValueError("Provide 1-100 segments.")
        values = [float(segment["value"]) for segment in segments]
        if any(not math.isfinite(value) or value < 0 for value in values):
            raise ValueError("Segment values must be finite and non-negative.")
        total_value = sum(values)
        if not math.isfinite(total_value) or total_value <= 0:
            raise ValueError("Total segment value must be greater than zero and finite.")
        codes = {str(segment["sic_code"]) for segment in segments}
        benchmarks = {}
        for row in db.scalars(select(SectorMacroSensitivityBenchmark).where(
            SectorMacroSensitivityBenchmark.market == market,
            SectorMacroSensitivityBenchmark.country == country,
            SectorMacroSensitivityBenchmark.sic_code.in_(codes),
        )):
            if row.sic_code in benchmarks:
                raise ValueError("Ambiguous benchmark selection; resolve duplicate market/country/SIC rows.")
            benchmarks[row.sic_code] = row

        contributions = dict.fromkeys(COEFFICIENTS, 0.0)
        coverage = dict.fromkeys(COEFFICIENTS, 0.0)
        exposures, missing = [], []
        covered_weight = 0.0
        for segment, value in zip(segments, values):
            weight = value / total_value
            if weight == 0:
                continue
            sic_code = str(segment["sic_code"])
            benchmark = benchmarks.get(sic_code)
            if benchmark is None:
                missing.append({"name": segment["name"], "sic_code": sic_code, "weight": round(weight, 10)})
                continue
            covered_weight += weight
            metrics = {}
            for field, column in COEFFICIENTS.items():
                coefficient = getattr(benchmark, column)
                usable = coefficient is not None and math.isfinite(coefficient)
                metrics[field] = coefficient if usable else None
                if usable:
                    contribution = weight * coefficient
                    if not math.isfinite(contribution + contributions[field]):
                        raise ValueError("Weighted sensitivity exceeds the supported finite range.")
                    contributions[field] += contribution
                    coverage[field] += weight
            exposures.append({
                "name": segment["name"], "sic_code": sic_code, "weight": round(weight, 10),
                "market": benchmark.market, "country": benchmark.country,
                "classification_system": benchmark.classification_system,
                "currency_context": benchmark.currency_context, "industry_name": benchmark.industry_name,
                "source_file": benchmark.source_file, "source_record_id": benchmark.id,
                "recorded_at": benchmark.created_at.isoformat() if benchmark.created_at else None,
                **metrics,
            })
        if not exposures:
            raise LookupError("No SIC macro sensitivity benchmarks found for submitted segments.")
        weighted = {field: round(contributions[field], 10) if math.isclose(coverage[field], 1, abs_tol=1e-9) else None
                    for field in COEFFICIENTS}
        warnings = [
            "Bottom-up sensitivity uses sector-level benchmarks, not company-specific regression output.",
            "This output does not automatically change valuation assumptions.",
            "Segment values are User Assumptions; use a consistent currency and valuation basis.",
            "Operating-income sensitivity is unavailable: segment value weights do not establish operating-income weights.",
        ]
        if missing:
            warnings.append("Missing SIC benchmark coverage for: " + ", ".join(row["sic_code"] for row in missing) + ".")
        for field in COEFFICIENTS:
            if weighted[field] is None:
                warnings.append(f"{field}: {coverage[field]:.1%} of segment value has a usable coefficient; the full-company estimate is unavailable.")
        if weighted["duration"] is not None and weighted["duration"] < 0:
            warnings.append(NEGATIVE_DURATION_WARNING)
        complete = all(value is not None for value in weighted.values())
        return {
            "method": "bottom_up", "market": market, "country": country, "observation_count": None, **weighted,
            "firm_value": weighted, "operating_income": dict.fromkeys(COEFFICIENTS),
            "duration_magnitude": duration_magnitude(weighted["duration"]),
            "duration_interpretation": duration_interpretation(weighted["duration"]),
            "covered_weight": round(covered_weight, 10),
            "metric_coverage": {key: round(value, 10) for key, value in coverage.items()},
            "covered_contributions": {key: round(value, 10) for key, value in contributions.items()},
            "confidence": "medium" if complete else "low", "confidence_label": "medium" if complete else "low",
            "segment_exposures": exposures, "missing_segments": missing, "warnings": warnings,
            "claim_type": "Calculation", "basis": "User-supplied segment values weighted against selected sector benchmark records.",
            "formula": "Company sensitivity = sum(segment_value / total_segment_value * sector_sensitivity). Full-company estimates require 100% coefficient coverage. Covered contributions are partial sums, not missing-segment zero assumptions.",
        }
