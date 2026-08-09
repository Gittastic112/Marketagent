import { expect, test } from "@playwright/test";

import { backendData, createCompany, signIn } from "./helpers";

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

  await page.locator("#starting_revenue:visible").fill("1200");
  await page.getByRole("button", { name: "Save Draft" }).click();
  await expect(page.getByText("Draft saved")).toBeVisible();
  await page.getByRole("button", { name: "Reset starting_revenue to source" }).click();
  await expect(page.getByRole("button", { name: "Reset starting_revenue to source" })).toHaveCount(0);

  await page.getByRole("button", { name: "Refresh Sources" }).click();
  await expect(page.getByRole("heading", { name: "Model Settings" })).toBeVisible();

  await page.getByRole("button", { name: "Archive" }).click();
  await page.getByRole("button", { name: "Confirm archive" }).click();
  await expect(page).toHaveURL(`/companies/${company.id}/valuation`);

  await page.goto(`/companies/${company.id}/valuation/draft`);
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

  const models = await backendData<Array<{ name: string }>>(
    page,
    `/companies/${company.id}/valuation-models`,
  );
  expect(models.some((model) => model.name === `E2E Reviewed DCF ${unique}`)).toBeTruthy();
});
