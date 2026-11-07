"""Pure, non-writing single-factor regressions over explicit dated inputs."""
import math
import re
from datetime import date
from typing import Any


FACTORS = ("change_in_long_term_bond_rate", "gdp_growth", "inflation_change", "currency_change")


class TopDownMacroSensitivityService:
    @classmethod
    def calculate(cls, periods: list[dict[str, Any]], frequency: str) -> dict[str, Any]:
        if not 3 <= len(periods) <= 120:
            raise ValueError("At least 3 periods and at most 120 periods are required.")
        if frequency not in {"annual", "quarterly"}:
            raise ValueError("Frequency must be annual or quarterly.")
        labels = [str(row.get("period", "")).strip() for row in periods]
        kinds = {"year" if re.fullmatch(r"\d{4}", label) else "quarter" if re.fullmatch(r"\d{4}[- ]?Q[1-4]", label, re.I) else "date" for label in labels}
        if len(kinds) != 1 or (frequency == "quarterly" and "year" in kinds) or (frequency == "annual" and "quarter" in kinds):
            raise ValueError("Use consistent period labels that match the selected frequency.")
        keys = [cls._period_key(str(row.get("period", ""))) for row in periods]
        if any(current <= previous for previous, current in zip(keys, keys[1:])):
            raise ValueError("Periods must be unique and chronological.")
        intervals = [key.year if frequency == "annual" else key.year * 4 + (key.month - 1) // 3 for key in keys]
        if any(current != previous + 1 for previous, current in zip(intervals, intervals[1:])):
            raise ValueError("Periods must be consecutive at the selected frequency; align the macro series before regression.")
        if frequency == "annual" and len({key.month for key in keys}) != 1:
            raise ValueError("Annual period ends must use the same reporting month.")
        for period in periods:
            cls._firm_value(period)
            for field in ("operating_income", *FACTORS):
                cls._finite(period.get(field))
            for field in ("market_cap", "total_debt", "enterprise_value"):
                if period.get(field) is not None:
                    cls._finite(period[field])
                    if field in {"market_cap", "total_debt"} and cls._finite(period[field]) < 0:
                        raise ValueError("Market capitalization and total debt cannot be negative.")

        observations = cls._period_changes(periods)
        firm_value = cls._sensitivity_block([row["firm_value_change"] for row in observations], observations)
        operating_income = cls._sensitivity_block([row["operating_income_change"] for row in observations], observations)
        diagnostics = {factor: {"status": "no_variation" if len({row[factor] for row in observations}) == 1 else "estimated",
                               "observation_count": len(observations)} for factor in FACTORS}
        warnings = [
            "Regression output should be interpreted with caution because sample size is limited.",
            "Inputs are User Assumptions unless separately reviewed; regression does not establish causation or forecast accuracy.",
            "Firm value uses explicit enterprise value, otherwise market cap plus total debt; cash and other claims are not inferred.",
            "Periods must use consistent units, currency and macro-series direction. Changes belong to the ending period.",
        ]
        for factor, detail in diagnostics.items():
            if detail["status"] == "no_variation":
                warnings.append(f"{factor}: no observed variation, so its sensitivity is unavailable.")
        if len(observations) < 8:
            warnings.append("Fewer than 8 observations makes top-down regression especially noisy.")
        return {
            "method": "top_down", "frequency": frequency, "observation_count": len(observations),
            "firm_value": firm_value, "operating_income": operating_income,
            "confidence_label": "low" if len(observations) < 8 or any(d["status"] != "estimated" for d in diagnostics.values()) else "medium",
            "factor_diagnostics": diagnostics, "claim_type": "Calculation",
            "basis": "Explicit company values and aligned macro observations; separate single-factor OLS, not multivariate causal attribution.",
            "warnings": warnings,
            "formula": "Single-factor OLS: Change in Firm Value or Change in Operating Income = alpha + beta * macro_variable. Signed duration = -rate_slope; negative duration is retained. Constant factors are unavailable, not zero.",
        }

    @staticmethod
    def _finite(value: Any) -> float:
        if value is None or isinstance(value, bool):
            raise ValueError("Explicit finite inputs are required.")
        try:
            number = float(value)
        except (TypeError, ValueError):
            raise ValueError("Explicit finite inputs are required.") from None
        if not math.isfinite(number):
            raise ValueError("Explicit finite inputs are required.")
        return number

    @staticmethod
    def _period_key(label: str) -> date:
        label = label.strip()
        if re.fullmatch(r"\d{4}", label):
            return date(int(label), 12, 31)
        quarter = re.fullmatch(r"(\d{4})[- ]?Q([1-4])", label, flags=re.I)
        if quarter:
            return date(int(quarter[1]), int(quarter[2]) * 3, 1)
        return date.fromisoformat(label)

    @classmethod
    def _period_changes(cls, periods: list[dict[str, Any]]) -> list[dict[str, float]]:
        rows = []
        for previous, current in zip(periods, periods[1:]):
            previous_value = cls._firm_value(previous)
            previous_income = cls._finite(previous["operating_income"])
            if previous_value == 0 or previous_income == 0:
                raise ValueError("Previous firm value and operating income must be non-zero.")
            row = {"firm_value_change": (cls._firm_value(current) - previous_value) / abs(previous_value),
                   "operating_income_change": (cls._finite(current["operating_income"]) - previous_income) / abs(previous_income),
                   **{factor: cls._finite(current[factor]) for factor in FACTORS}}
            if not all(math.isfinite(value) for value in row.values()):
                raise ValueError("Period changes exceed the supported finite range.")
            rows.append(row)
        return rows

    @classmethod
    def _firm_value(cls, period: dict[str, Any]) -> float:
        if period.get("enterprise_value") is not None:
            return cls._finite(period["enterprise_value"])
        return cls._finite(cls._finite(period.get("market_cap")) + cls._finite(period.get("total_debt")))

    @classmethod
    def _sensitivity_block(cls, dependent_values: list[float], observations: list[dict[str, float]]) -> dict[str, float | None]:
        slopes = [cls._slope([row[factor] for row in observations], dependent_values) for factor in FACTORS]
        return {"rate_slope": slopes[0], "duration": -slopes[0] if slopes[0] is not None else None,
                "cyclicality": slopes[1], "inflation_sensitivity": slopes[2], "currency_sensitivity": slopes[3]}

    @staticmethod
    def _slope(x_values: list[float], y_values: list[float]) -> float | None:
        x_mean = sum(x_values) / len(x_values)
        y_mean = sum(y_values) / len(y_values)
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        try:
            denominator = sum((x - x_mean) ** 2 for x in x_values)
        except OverflowError:
            raise ValueError("Regression exceeds the supported finite range.") from None
        if not math.isfinite(numerator) or not math.isfinite(denominator):
            raise ValueError("Regression exceeds the supported finite range.")
        if denominator == 0:
            return None
        value = numerator / denominator
        if not math.isfinite(value):
            raise ValueError("Regression exceeds the supported finite range.")
        return round(value, 10)
