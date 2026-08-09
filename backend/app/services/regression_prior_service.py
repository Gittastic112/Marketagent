from __future__ import annotations

import math
from typing import Any

from sqlalchemy.orm import Session

from app.models.damodaran_fundamentals import RegressionModelCoefficient
from app.services.regression_model_catalog import RegressionModelSpec, get_regression_spec


class RegressionPriorService:
    """Calculate dated regression estimates only from verified source coefficients."""

    @staticmethod
    def _base_result(spec: RegressionModelSpec) -> dict[str, Any]:
        return {
            "prior_value": None,
            "formula": spec.formula,
            "model": spec.model_name,
            "claim_type": "Estimate",
            "confidence": spec.confidence,
            "source": spec.source_title,
            "source_path": spec.source_path,
            "source_as_of": spec.source_as_of,
            "adjusted_r_squared": spec.adjusted_r_squared,
            "input_units": dict(spec.input_units),
            "output_unit": spec.output_unit,
            "usable": spec.usable,
            "warnings": [],
        }

    @staticmethod
    def _validated_coefficients(
        db: Session,
        spec: RegressionModelSpec,
    ) -> tuple[dict[str, float] | None, list[str]]:
        rows = (
            db.query(RegressionModelCoefficient)
            .filter(
                RegressionModelCoefficient.model_name == spec.model_name,
                RegressionModelCoefficient.region == spec.region,
            )
            .all()
        )
        if not rows:
            return None, [
                f"COEFFICIENTS_NOT_SEEDED: Run scripts/seed_regressions.py for {spec.model_name}."
            ]

        coefficients = {row.variable_name.casefold(): row.coefficient_value for row in rows}
        expected_names = set(spec.coefficients)
        if set(coefficients) != expected_names or len(rows) != len(expected_names):
            return None, [
                f"COEFFICIENT_SET_INVALID: Stored variables for {spec.model_name} do not match the source PDF."
            ]

        for name, expected_value in spec.coefficients.items():
            if not math.isclose(coefficients[name], expected_value, rel_tol=0.0, abs_tol=1e-12):
                return None, [
                    f"COEFFICIENT_SOURCE_MISMATCH: Stored {name} for {spec.model_name} differs from the source PDF."
                ]
        return coefficients, []

    @classmethod
    def _calculate(
        cls,
        db: Session,
        spec: RegressionModelSpec,
        source_inputs: dict[str, float],
    ) -> dict[str, Any]:
        result = cls._base_result(spec)
        coefficients, validation_warnings = cls._validated_coefficients(db, spec)
        if coefficients is None:
            result["warnings"] = validation_warnings
            return result

        fit_warning = (
            f"LOW_EXPLANATORY_POWER: Adjusted R-squared is {spec.adjusted_r_squared:.3f}; "
            "treat this dated regression as a low-confidence prior, not a target."
        )
        if not spec.usable:
            result["warnings"] = [
                f"MODEL_NOT_USABLE: {spec.model_name} is disabled because its explanatory power is not decision-useful.",
                fit_warning,
            ]
            return result

        raw_output = coefficients["intercept"] + sum(
            coefficients[name] * value for name, value in source_inputs.items()
        )
        if spec.floor_at_zero:
            raw_output = max(0.0, raw_output)

        if spec.kind in {"debt_ratio", "dividend_yield"}:
            prior_value = raw_output / 100.0
        else:
            prior_value = raw_output

        warnings = [fit_warning]
        if prior_value > 1.0:
            warnings.append(
                "OUTPUT_OUT_OF_RANGE: The regression produced a value above 100%; review inputs and do not apply it automatically."
            )
        result["prior_value"] = prior_value
        result["warnings"] = warnings
        return result

    @classmethod
    def calculate_debt_ratio_prior(
        cls,
        db: Session,
        effective_tax_rate: float,
        expected_eps_growth: float,
        institutional_holdings: float,
        company_age_years: float,
        region: str = "Global",
    ) -> dict[str, Any]:
        spec = get_regression_spec("debt_ratio", region)
        if spec is None:
            raise ValueError(f"Unsupported debt-ratio regression region: {region}")
        return cls._calculate(
            db,
            spec,
            {
                "effective_tax_rate_pct": effective_tax_rate * 100.0,
                "expected_eps_growth": expected_eps_growth,
                "institutional_holdings": institutional_holdings,
                "company_age_years": company_age_years,
            },
        )

    @classmethod
    def calculate_dividend_yield_prior(
        cls,
        db: Session,
        effective_tax_rate: float,
        expected_eps_growth: float,
        company_age_years: float,
        beta: float,
        region: str = "Global",
    ) -> dict[str, Any]:
        spec = get_regression_spec("dividend_yield", region)
        if spec is None:
            raise ValueError(f"Unsupported dividend-yield regression region: {region}")
        return cls._calculate(
            db,
            spec,
            {
                "effective_tax_rate_pct": effective_tax_rate * 100.0,
                "expected_eps_growth": expected_eps_growth,
                "company_age_years": company_age_years,
                "beta": beta,
            },
        )

    @classmethod
    def calculate_dividend_payout_prior(
        cls,
        db: Session,
        beta: float,
        return_on_equity: float,
        region: str = "Global",
    ) -> dict[str, Any]:
        spec = get_regression_spec("dividend_payout", region)
        if spec is None:
            raise ValueError(f"Unsupported dividend-payout regression region: {region}")
        return cls._calculate(
            db,
            spec,
            {"beta": beta, "return_on_equity": return_on_equity},
        )
