"""Compatibility wrapper for the canonical source-backed regression seed."""

from seed_regressions import seed_regression_coefficients


if __name__ == "__main__":
    result = seed_regression_coefficients()
    print(
        "Synchronized source-backed January 2025 regressions: "
        f"{result['models']} models and {result['coefficients']} coefficients."
    )
