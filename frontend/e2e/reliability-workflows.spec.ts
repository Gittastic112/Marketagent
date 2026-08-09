import { expect, test } from "@playwright/test";

import { backendData, createCompany, signIn } from "./helpers";


test("valuation edits invalidate review and stale writes surface a reload action", async ({ page }) => {
  await signIn(page);
  const unique = Date.now().toString().slice(-7);
  const company = await createCompany(page, {
    ticker: `W${unique}`,
    local_symbol: `W${unique}`,
    name: "Valuation Conflict E2E Fixture",
  });
  const draft = await backendData<{
    id: number;
    updated_at: string;
    reviewed_fields_json: string[];
  }>(page, `/companies/${company.id}/valuation-drafts`, { method: "POST", data: {} });

  await page.goto(`/companies/${company.id}/valuation/draft`);
  const startingRevenue = page.locator("#starting_revenue:visible");
  const startingRevenueField = startingRevenue.locator("xpath=..");
  const review = startingRevenueField.locator('input[name="reviewed_field"]');
  await startingRevenue.fill("1000");
  await review.check();
  await expect(review).toBeChecked();
  await startingRevenue.fill("1200");
  await expect(review).not.toBeChecked();

  await backendData(page, `/valuation-drafts/${draft.id}`, {
    method: "PATCH",
    data: {
      assumptions_patch: { cash: 25 },
      reviewed_fields: draft.reviewed_fields_json,
      expected_updated_at: draft.updated_at,
    },
  });
  await page.getByRole("button", { name: "Save Draft" }).click();
  await expect(page.getByText(/changed since it was loaded\. Reload before saving\./)).toBeVisible();
});


test("dashboard exposes partial portfolio analytics and the corrective price action", async ({ page }) => {
  await signIn(page);
  const unique = Date.now().toString().slice(-7);
  const ticker = `D${unique}`;
  const company = await createCompany(page, {
    ticker,
    local_symbol: ticker,
    name: "Partial Dashboard E2E Fixture",
  });
  const portfolio = await backendData<{ id: number }>(page, "/portfolios", {
    method: "POST",
    data: { name: `Partial Portfolio ${unique}`, base_currency: "USD" },
  });
  await backendData(page, "/portfolio-holdings", {
    method: "POST",
    data: {
      portfolio_id: portfolio.id,
      company_id: company.id,
      ticker,
      quantity: 5,
      average_cost: 100,
      currency: "USD",
      as_of_date: "2026-07-31",
    },
  });

  await page.goto("/");
  await expect(page.getByRole("main").getByText(/Default portfolio analytics are partial until every holding has a dated market price\./).first()).toBeVisible();
  await expect(page.getByRole("link", { name: "Add Prices" })).toHaveAttribute("href", "/market-prices");
});
