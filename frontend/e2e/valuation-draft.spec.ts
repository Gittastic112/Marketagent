import { expect, test } from "@playwright/test";

import { backendData, createCompany, expandDraftSections, signIn } from "./helpers";

const ASSUMPTIONS: Record<string, string> = {
  starting_revenue: "1000",
  current_operating_margin: "0.20",
  target_operating_margin: "0.24",
  tax_rate: "0.21",
  sales_to_capital_ratio: "2",
  starting_invested_capital: "500",
  risk_free_rate: "0.04",
  equity_risk_premium: "0.05",
  beta: "1",
  cost_of_equity: "0.09",
  pre_tax_cost_of_debt: "0.05",
  debt_to_capital: "0.20",
  equity_to_capital: "0.80",
  wacc_start: "0.08",
  wacc_terminal: "0.07",
  terminal_growth_rate: "0.03",
  terminal_roic: "0.12",
  cash: "100",
  debt: "50",
  minority_interests: "0",
  preferred_stock: "0",
  employee_options_value: "0",
  diluted_shares: "100",
  current_market_price: "10",
};

test("valuation draft save, reset, refresh, archive, and promotion", async ({ page }) => {
  await signIn(page);
  const unique = Date.now().toString().slice(-7);
  const company = await createCompany(page, {
    ticker: `V${unique}`,
    local_symbol: `V${unique}`,
    name: "Valuation E2E Fixture",
  });

  await page.goto(`/companies/${company.id}/valuation/draft`);
  await expect(
    page.getByRole("heading", { name: "Draft New Valuation Model: Valuation E2E Fixture" }),
  ).toBeVisible();
  await expandDraftSections(page);

  await page.locator("#starting_revenue:visible").fill("1200");
  await page.getByRole("button", { name: "Save Draft" }).click();
  await expect(page.getByText("Draft saved")).toBeVisible();
  await page.getByRole("button", { name: "Reset starting_revenue to source" }).click();
  await expect(page.getByRole("button", { name: "Reset starting_revenue to source" })).toHaveCount(0);

  await page.getByRole("button", { name: "Refresh Stored Inputs" }).click();
  await expect(page.getByRole("heading", { name: "Model Settings" })).toBeVisible();

  await page.getByRole("button", { name: "Archive" }).click();
  await page.getByRole("button", { name: "Confirm archive" }).click();
  await expect(page).toHaveURL(`/companies/${company.id}/valuation`);

  await page.goto(`/companies/${company.id}/valuation/draft`);
  await expandDraftSections(page);
  await expect(page.locator("#starting_revenue:visible")).toHaveCount(1);
  for (const [field, value] of Object.entries(ASSUMPTIONS)) {
    await page.locator(`#${field}:visible`).fill(value);
  }
  await page.locator("#revenue-growth:visible").fill(
    JSON.stringify({ 1: 0.10, 2: 0.08, 3: 0.06, 4: 0.05, 5: 0.04 }),
  );

  const reviewCheckboxes = page.locator('input[name="reviewed_field"]');
  const reviewCount = await reviewCheckboxes.count();
  expect(reviewCount).toBeGreaterThan(0);
  for (let index = 0; index < reviewCount; index += 1) {
    await reviewCheckboxes.nth(index).check();
  }
  await expect(page.getByText("Ready to create")).toBeVisible();

  await page.locator("#model-name:visible").fill(`E2E Reviewed DCF ${unique}`);
  await page.getByRole("button", { name: "Confirm and Create Model" }).click();
  await expect(page).toHaveURL(new RegExp(`/companies/${company.id}/valuation/\\d+$`));
  await expect(page.getByText(`E2E Reviewed DCF ${unique}`, { exact: false })).toBeVisible();

  await expect(page.getByText("User Assumption", { exact: true })).toBeVisible();
  await page.getByLabel("Model name").fill(`E2E Updated DCF ${unique}`);
  await page.getByLabel("Description").fill("Metadata update from the complete valuation workflow");
  await page.getByRole("button", { name: "Save model details" }).click();
  await expect(page.getByText(`E2E Updated DCF ${unique}`, { exact: false })).toBeVisible();

  await page.getByRole("navigation", { name: "Valuation model sections" })
    .getByRole("button", { name: "Payouts & Cash Return", exact: true }).click();
  await page.locator("#capex:visible").fill("120");
  await page.locator("#depreciation:visible").fill("80");
  await page.locator("#change_in_nwc:visible").fill("25");
  await page.locator("#buybacks:visible").fill("15");
  await page.locator("#new_debt_issued:visible").fill("40");
  await page.getByRole("button", { name: "Save & Run Valuation" }).click();
  await expect(page.getByText("Assumptions saved and valuation recalculated.")).toBeVisible();

  const detailUrl = new URL(page.url());
  const modelId = Number(detailUrl.pathname.split("/").at(-1));
  const assumptionSets = await backendData<Array<{ capex: number; depreciation: number; buybacks: number }>>(
    page,
    `/valuation-models/${modelId}/assumptions`,
  );
  expect(assumptionSets[0].capex).toBe(120);
  expect(assumptionSets[0].depreciation).toBe(80);
  expect(assumptionSets[0].buybacks).toBe(15);

  await page.getByRole("navigation", { name: "Valuation model sections" })
    .getByRole("button", { name: "Sensitivity Tables", exact: true }).click();
  await expect(page.locator(".sensitivity-card:visible")).toHaveCount(6);
  await expect(page.locator(".sensitivity-card:visible").first().getByText(/Canonical FCFF sensitivity v2/)).toBeVisible();
  await expect(page.getByText(/Colors compare calculated values with the saved assumed market price/)).toBeVisible();
  const saved = await backendData<Array<{
    id: number; outputs: { intrinsic_value_per_share: number };
    sensitivity_tables: Array<{ x_axis_json: { values: number[] }; y_axis_json: { values: number[] }; values_json: Record<string, Record<string, number | null>> }>;
  }>>(page, `/valuation-models/${modelId}/assumptions`);
  for (const table of saved[0].sensitivity_tables) {
    const x = Number(table.x_axis_json.values[2].toFixed(4));
    const y = Number(table.y_axis_json.values[2].toFixed(4));
    const row = Object.entries(table.values_json).find(([key]) => Number(key) === y)![1];
    const center = Object.entries(row).find(([key]) => Number(key) === x)![1];
    expect(center).toBeCloseTo(saved[0].outputs.intrinsic_value_per_share, 8);
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator(".sensitivity-card:visible")).toHaveCount(6);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1)).toBe(true);
  const matrix = page.getByRole("region", { name: /sensitivity table$/ }).first();
  await matrix.focus();
  await expect(matrix).toBeFocused();
  await matrix.press("ArrowRight");
  await expect.poll(() => matrix.evaluate(element => element.scrollLeft)).toBeGreaterThan(0);
  await page.screenshot({ path: test.info().outputPath("sensitivity-mobile.png"), fullPage: true });
  await page.setViewportSize({ width: 1440, height: 1000 });

  await page.getByRole("navigation", { name: "Valuation model sections" })
    .getByRole("button", { name: "Real Options", exact: true }).click();
  await expect(page.getByText(/^Experimental supplemental analysis/)).toBeVisible();
  await expect(page.getByRole("button", { name: "Calculate Real Option Value", exact: true })).toBeDisabled();

  await page.goto(`/companies/${company.id}/valuation`);
  await expect(page.getByRole("columnheader", { name: "Model readiness" })).toBeVisible();
  const savedModelRow = page.getByRole("row").filter({
    has: page.getByRole("link", { name: `E2E Updated DCF ${unique}`, exact: true }),
  });
  await expect(savedModelRow.getByText("Calculated", { exact: true })).toBeVisible();

  const models = await backendData<Array<{ name: string }>>(
    page,
    `/companies/${company.id}/valuation-models`,
  );
  expect(models.some((model) => model.name === `E2E Updated DCF ${unique}`)).toBeTruthy();
});
