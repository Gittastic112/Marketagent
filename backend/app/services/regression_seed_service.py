from __future__ import annotations

from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.damodaran_fundamentals import RegressionModelCoefficient
from app.services.regression_model_catalog import (
    REGRESSION_MODEL_SPECS,
    SOURCE_VERSION_DATE,
    canonical_model_name,
)


def sync_source_backed_regression_coefficients(db: Session) -> dict[str, int]:
    """Idempotently replace only the six source-backed January 2025 models."""

    rows_by_key: dict[tuple[str, str], list[RegressionModelCoefficient]] = defaultdict(list)
    deleted = 0

    for row in db.query(RegressionModelCoefficient).all():
        canonical_name = canonical_model_name(row.model_name)
        if canonical_name is None:
            continue
        rows_by_key[(canonical_name, row.variable_name.casefold())].append(row)

    expected_keys = {
        (spec.model_name, variable_name)
        for spec in REGRESSION_MODEL_SPECS
        for variable_name in spec.coefficients
    }

    for key, rows in list(rows_by_key.items()):
        if key not in expected_keys:
            for row in rows:
                db.delete(row)
                deleted += 1
            rows_by_key.pop(key)

    created = 0
    updated = 0
    unchanged = 0

    for spec in REGRESSION_MODEL_SPECS:
        for variable_name, coefficient_value in spec.coefficients.items():
            key = (spec.model_name, variable_name)
            candidates = rows_by_key.get(key, [])
            row = candidates[0] if candidates else None
            for duplicate in candidates[1:]:
                db.delete(duplicate)
                deleted += 1

            if row is None:
                db.add(
                    RegressionModelCoefficient(
                        model_name=spec.model_name,
                        variable_name=variable_name,
                        coefficient_value=coefficient_value,
                        region=spec.region,
                        version_date=SOURCE_VERSION_DATE,
                    )
                )
                created += 1
                continue

            changed = False
            expected = {
                "model_name": spec.model_name,
                "variable_name": variable_name,
                "coefficient_value": coefficient_value,
                "region": spec.region,
                "version_date": SOURCE_VERSION_DATE,
            }
            for field, value in expected.items():
                current_value = getattr(row, field)
                values_match = current_value == value
                if field == "version_date" and current_value is not None:
                    values_match = current_value.date() == value.date()
                if not values_match:
                    setattr(row, field, value)
                    changed = True
            if changed:
                updated += 1
            else:
                unchanged += 1

    db.flush()
    return {
        "models": len(REGRESSION_MODEL_SPECS),
        "coefficients": sum(len(spec.coefficients) for spec in REGRESSION_MODEL_SPECS),
        "created": created,
        "updated": updated,
        "deleted": deleted,
        "unchanged": unchanged,
    }
