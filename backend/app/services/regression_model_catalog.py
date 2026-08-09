from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping


SOURCE_VERSION_DATE = datetime(2025, 1, 1, tzinfo=timezone.utc)


@dataclass(frozen=True)
class RegressionModelSpec:
    kind: str
    model_name: str
    region: str
    coefficients: Mapping[str, float]
    formula: str
    input_units: Mapping[str, str]
    output_unit: str
    adjusted_r_squared: float
    confidence: str
    usable: bool
    source_title: str
    source_path: str
    source_as_of: str = "2025-01"
    floor_at_zero: bool = True


DEBT_SOURCE = "Debt Ratio Regression: January 2025"
DEBT_SOURCE_PATH = "damodaran_knowledge_base_v1/raw/articles/debt regression.pdf"
DIVIDEND_SOURCE = "Dividend Regressions: January 2025"
DIVIDEND_SOURCE_PATH = "damodaran_knowledge_base_v1/raw/articles/global regression debt.pdf"


REGRESSION_MODEL_SPECS: tuple[RegressionModelSpec, ...] = (
    RegressionModelSpec(
        kind="debt_ratio",
        model_name="us_debt_ratio",
        region="US",
        coefficients={
            "intercept": 1.666,
            "effective_tax_rate_pct": -0.176,
            "expected_eps_growth": -26.978,
            "institutional_holdings": 18.519,
            "company_age_years": 0.065,
        },
        formula="1.666 - 0.176*TaxRatePct - 26.978*EPSGrowth + 18.519*InstitutionalHoldings + 0.065*CompanyAge",
        input_units={
            "effective_tax_rate": "decimal",
            "expected_eps_growth": "decimal",
            "institutional_holdings": "decimal",
            "company_age_years": "years",
        },
        output_unit="decimal_ratio",
        adjusted_r_squared=0.190,
        confidence="low",
        usable=True,
        source_title=DEBT_SOURCE,
        source_path=DEBT_SOURCE_PATH,
    ),
    RegressionModelSpec(
        kind="debt_ratio",
        model_name="global_debt_ratio",
        region="Global",
        coefficients={
            "intercept": 17.419,
            "effective_tax_rate_pct": -0.057,
            "expected_eps_growth": -20.401,
            "institutional_holdings": -2.153,
            "company_age_years": 0.033,
        },
        formula="17.419 - 0.057*TaxRatePct - 20.401*EPSGrowth - 2.153*InstitutionalHoldings + 0.033*CompanyAge",
        input_units={
            "effective_tax_rate": "decimal",
            "expected_eps_growth": "decimal",
            "institutional_holdings": "decimal",
            "company_age_years": "years",
        },
        output_unit="decimal_ratio",
        adjusted_r_squared=0.065,
        confidence="low",
        usable=True,
        source_title=DEBT_SOURCE,
        source_path=DEBT_SOURCE_PATH,
    ),
    RegressionModelSpec(
        kind="dividend_yield",
        model_name="us_dividend_yield",
        region="US",
        coefficients={
            "intercept": 2.396,
            "effective_tax_rate_pct": -0.017,
            "expected_eps_growth": -1.838,
            "company_age_years": 0.008,
            "beta": -1.124,
        },
        formula="2.396 - 0.017*TaxRatePct - 1.838*EPSGrowth + 0.008*CompanyAge - 1.124*Beta",
        input_units={
            "effective_tax_rate": "decimal",
            "expected_eps_growth": "decimal",
            "company_age_years": "years",
            "beta": "ratio",
        },
        output_unit="decimal_yield",
        adjusted_r_squared=0.346,
        confidence="low",
        usable=True,
        source_title=DIVIDEND_SOURCE,
        source_path=DIVIDEND_SOURCE_PATH,
    ),
    RegressionModelSpec(
        kind="dividend_yield",
        model_name="global_dividend_yield",
        region="Global",
        coefficients={
            "intercept": 1.835,
            "effective_tax_rate_pct": 0.035,
            "expected_eps_growth": -3.603,
            "company_age_years": 0.004,
            "beta": -0.279,
        },
        formula="1.835 + 0.035*TaxRatePct - 3.603*EPSGrowth + 0.004*CompanyAge - 0.279*Beta",
        input_units={
            "effective_tax_rate": "decimal",
            "expected_eps_growth": "decimal",
            "company_age_years": "years",
            "beta": "ratio",
        },
        output_unit="decimal_yield",
        adjusted_r_squared=0.146,
        confidence="low",
        usable=True,
        source_title=DIVIDEND_SOURCE,
        source_path=DIVIDEND_SOURCE_PATH,
    ),
    RegressionModelSpec(
        kind="dividend_payout",
        model_name="us_dividend_payout",
        region="US",
        coefficients={
            "intercept": 0.990,
            "beta": -0.478,
            "return_on_equity": -0.115,
        },
        formula="0.990 - 0.478*Beta - 0.115*ROE",
        input_units={"beta": "ratio", "return_on_equity": "decimal"},
        output_unit="decimal_ratio",
        adjusted_r_squared=0.025,
        confidence="not_usable",
        usable=False,
        source_title=DIVIDEND_SOURCE,
        source_path=DIVIDEND_SOURCE_PATH,
    ),
    RegressionModelSpec(
        kind="dividend_payout",
        model_name="global_dividend_payout",
        region="Global",
        coefficients={
            "intercept": 0.733,
            "beta": -0.182,
            "return_on_equity": 0.253,
        },
        formula="0.733 - 0.182*Beta + 0.253*ROE",
        input_units={"beta": "ratio", "return_on_equity": "decimal"},
        output_unit="decimal_ratio",
        adjusted_r_squared=0.000,
        confidence="not_usable",
        usable=False,
        source_title=DIVIDEND_SOURCE,
        source_path=DIVIDEND_SOURCE_PATH,
    ),
)


SPECS_BY_KEY = {(spec.kind, spec.region.casefold()): spec for spec in REGRESSION_MODEL_SPECS}
SPECS_BY_MODEL = {spec.model_name: spec for spec in REGRESSION_MODEL_SPECS}


LEGACY_MODEL_ALIASES = {
    "global_debt_ratio": "global_debt_ratio",
    "us_debt_ratio": "us_debt_ratio",
    "global_dividend_yield": "global_dividend_yield",
    "us_dividend_yield": "us_dividend_yield",
    "global_dividend_payout": "global_dividend_payout",
    "us_dividend_payout": "us_dividend_payout",
}


def canonical_model_name(model_name: str) -> str | None:
    return LEGACY_MODEL_ALIASES.get(model_name.casefold())


def get_regression_spec(kind: str, region: str) -> RegressionModelSpec | None:
    return SPECS_BY_KEY.get((kind, region.casefold()))
