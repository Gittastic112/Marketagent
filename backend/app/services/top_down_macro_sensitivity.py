from typing import Any


class TopDownMacroSensitivityService:
    @classmethod
    def calculate(cls, periods: list[dict[str, Any]], frequency: str) -> dict[str, Any]:
        if len(periods) < 3:
            raise ValueError("At least 3 periods are required for top-down macro sensitivity.")

        observations = cls._period_changes(periods)
        firm_value_changes = [row["firm_value_change"] for row in observations]
        operating_income_changes = [row["operating_income_change"] for row in observations]

        firm_value = cls._sensitivity_block(firm_value_changes, observations)
        operating_income = cls._sensitivity_block(operating_income_changes, observations)

        warnings = [
            "Regression output should be interpreted with caution because sample size is limited."
        ]
        if len(observations) < 8:
            confidence_label = "low"
            warnings.append("Fewer than 8 observations makes top-down regression especially noisy.")
        elif len(observations) < 15:
            confidence_label = "medium"
        else:
            confidence_label = "high"

        return {
            "method": "top_down",
            "frequency": frequency,
            "observation_count": len(observations),
            "firm_value": firm_value,
            "operating_income": operating_income,
            "confidence_label": confidence_label,
            "warnings": warnings,
            "formula": (
                "Single-factor OLS: Change in Firm Value or Change in Operating Income "
                "= alpha + beta * macro_variable. Duration = max(0, -rate_slope)."
            ),
        }

    @classmethod
    def _period_changes(cls, periods: list[dict[str, Any]]) -> list[dict[str, float]]:
        rows: list[dict[str, float]] = []
        for previous, current in zip(periods, periods[1:]):
            previous_firm_value = cls._firm_value(previous)
            current_firm_value = cls._firm_value(current)
            previous_operating_income = float(previous["operating_income"])
            current_operating_income = float(current["operating_income"])

            if previous_firm_value == 0 or previous_operating_income == 0:
                raise ValueError("Previous firm value and operating income must be non-zero.")

            rows.append(
                {
                    "firm_value_change": (current_firm_value - previous_firm_value)
                    / abs(previous_firm_value),
                    "operating_income_change": (
                        current_operating_income - previous_operating_income
                    )
                    / abs(previous_operating_income),
                    "change_in_long_term_bond_rate": float(
                        current["change_in_long_term_bond_rate"]
                    ),
                    "gdp_growth": float(current["gdp_growth"]),
                    "inflation_change": float(current["inflation_change"]),
                    "currency_change": float(current["currency_change"]),
                }
            )
        return rows

    @staticmethod
    def _firm_value(period: dict[str, Any]) -> float:
        enterprise_value = period.get("enterprise_value")
        if enterprise_value is not None:
            return float(enterprise_value)
        return float(period["market_cap"]) + float(period["total_debt"])

    @classmethod
    def _sensitivity_block(
        cls,
        dependent_values: list[float],
        observations: list[dict[str, float]],
    ) -> dict[str, float]:
        rate_slope = cls._slope(
            [row["change_in_long_term_bond_rate"] for row in observations],
            dependent_values,
        )
        gdp_slope = cls._slope([row["gdp_growth"] for row in observations], dependent_values)
        inflation_slope = cls._slope(
            [row["inflation_change"] for row in observations],
            dependent_values,
        )
        currency_slope = cls._slope(
            [row["currency_change"] for row in observations],
            dependent_values,
        )

        return {
            "rate_slope": round(rate_slope, 10),
            "duration": round(max(0.0, -rate_slope), 10),
            "cyclicality": round(gdp_slope, 10),
            "inflation_sensitivity": round(inflation_slope, 10),
            "currency_sensitivity": round(currency_slope, 10),
        }

    @staticmethod
    def _slope(x_values: list[float], y_values: list[float]) -> float:
        x_mean = sum(x_values) / len(x_values)
        y_mean = sum(y_values) / len(y_values)
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        if denominator == 0:
            return 0.0
        return numerator / denominator
