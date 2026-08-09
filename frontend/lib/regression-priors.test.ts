import assert from "node:assert/strict";
import test from "node:test";

import { buildDebtRatioPriorRequest } from "./regression-priors.ts";


test("builds the source-aligned debt-ratio request without proxies", () => {
  const result = buildDebtRatioPriorRequest({
    effectiveTaxRate: "0.25",
    expectedEpsGrowthPct: "12",
    institutionalHoldingsPct: "30",
    companyAgeYears: "37",
    region: "Global",
  });

  assert.deepEqual(result, {
    payload: {
      effective_tax_rate: 0.25,
      expected_eps_growth: 0.12,
      institutional_holdings: 0.30,
      company_age_years: 37,
      region: "Global",
    },
    error: null,
  });
});


test("rejects missing and out-of-range source inputs", () => {
  assert.equal(buildDebtRatioPriorRequest({
    effectiveTaxRate: "0.25",
    expectedEpsGrowthPct: "",
    institutionalHoldingsPct: "30",
    companyAgeYears: "37",
    region: "Global",
  }).payload, null);

  assert.equal(buildDebtRatioPriorRequest({
    effectiveTaxRate: "0.25",
    expectedEpsGrowthPct: "12",
    institutionalHoldingsPct: "130",
    companyAgeYears: "37",
    region: "Global",
  }).payload, null);
});
