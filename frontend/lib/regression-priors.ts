import type { DebtRatioPriorRequest } from "./api";


export type DebtRatioPriorFormValues = {
  effectiveTaxRate: string;
  expectedEpsGrowthPct: string;
  institutionalHoldingsPct: string;
  companyAgeYears: string;
  region: "Global" | "US";
};


export type DebtRatioPriorBuildResult =
  | { payload: DebtRatioPriorRequest; error: null }
  | { payload: null; error: string };


function requiredNumber(value: string): number | null {
  if (value.trim() === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}


export function buildDebtRatioPriorRequest(
  values: DebtRatioPriorFormValues,
): DebtRatioPriorBuildResult {
  const effectiveTaxRate = requiredNumber(values.effectiveTaxRate);
  const expectedEpsGrowthPct = requiredNumber(values.expectedEpsGrowthPct);
  const institutionalHoldingsPct = requiredNumber(values.institutionalHoldingsPct);
  const companyAgeYears = requiredNumber(values.companyAgeYears);

  if (
    effectiveTaxRate === null
    || expectedEpsGrowthPct === null
    || institutionalHoldingsPct === null
    || companyAgeYears === null
  ) {
    return { payload: null, error: "Enter all regression inputs." };
  }
  if (effectiveTaxRate < 0 || effectiveTaxRate > 1) {
    return { payload: null, error: "Effective tax rate must be between 0 and 1." };
  }
  if (expectedEpsGrowthPct < -100 || expectedEpsGrowthPct > 1000) {
    return { payload: null, error: "Expected EPS growth must be between -100% and 1000%." };
  }
  if (institutionalHoldingsPct < 0 || institutionalHoldingsPct > 100) {
    return { payload: null, error: "Institutional holdings must be between 0% and 100%." };
  }
  if (companyAgeYears < 0 || companyAgeYears > 500) {
    return { payload: null, error: "Company age must be between 0 and 500 years." };
  }

  return {
    payload: {
      effective_tax_rate: effectiveTaxRate,
      expected_eps_growth: expectedEpsGrowthPct / 100,
      institutional_holdings: institutionalHoldingsPct / 100,
      company_age_years: companyAgeYears,
      region: values.region,
    },
    error: null,
  };
}
