import { expect, test } from "@playwright/test";

import { backendData, createCompany, expandDraftSections, signIn } from "./helpers";


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
  await expect(page.getByRole("button", {name: "Create draft", exact: true})).toHaveCount(0);
  expect((await backendData<{id: number}>(page, `/companies/${company.id}/valuation-drafts/current`)).id).toBe(draft.id);
  await expandDraftSections(page);
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
  await expect(page.getByRole("main").getByText(/changed since it was loaded\. Reload before saving\./)).toBeVisible();
});


test("dashboard exposes a partial stored snapshot and its portfolio price gaps", async ({ page }) => {
  await signIn(page);
  const unique = Date.now().toString().slice(-7);
  const ticker = `D${unique}`;
  const company = await createCompany(page, {
    ticker,
    local_symbol: ticker,
    name: "Mock Data Partial Dashboard E2E Fixture",
  });
  // Use explicit dashboard selection and a fully recorded isolated ledger.
  // A buy creates its holding; a manual opening would double this position.
  const portfolio = await backendData<{id:number}>(page, "/portfolios", {method:"POST",
    data:{name:`Mock Data partial dashboard ${unique}`,base_currency:"USD"}});
  const asOfDate = "2026-08-01";

  let snapshotId: number | undefined;
  const transactionIds: number[] = [];
  try {
    for (const activity of [
      { company_id: null, ticker: "CASH", transaction_type: "deposit", quantity: 500, price: 0 },
      { company_id: company.id, ticker, transaction_type: "buy", quantity: 5, price: 100 },
    ]) {
      const transaction = await backendData<{ id: number }>(page, "/portfolio-transactions", {
        method: "POST", data: { ...activity, portfolio_id: portfolio.id, fees: 0, currency: "USD",
          transaction_date: asOfDate, notes: "Mock Data temporary purchase for missing-price browser verification." },
      });
      transactionIds.push(transaction.id);
    }
    const snapshot = await backendData<{
      id: number;
      calculation_status: string;
      missing_price_tickers_json: string[];
    }>(page, `/portfolios/${portfolio.id}/snapshots/capture?as_of_date=${asOfDate}`, { method: "POST" });
    snapshotId = snapshot.id;
    expect(snapshot.calculation_status).toBe("partial");
    expect(snapshot.missing_price_tickers_json).toContain(ticker);

    await page.goto(`/?portfolio_id=${portfolio.id}`);
    await expect(page.getByRole("main").getByText("The latest portfolio snapshot is partial; missing prices or FX remain unavailable.", { exact: true })).toBeVisible();
    const portfolioLink = page.getByRole("region", { name: "Research summary" }).getByRole("link", { name: /Portfolio value/ });
    await expect(portfolioLink).toContainText(`Stored snapshot · ${asOfDate}`);
    await expect(portfolioLink).toContainText("Not available");
    await expect(portfolioLink).toHaveAttribute("href", `/portfolio/${portfolio.id}`);
    await portfolioLink.click();
    const missingPriceRow = page.getByRole("row").filter({ has: page.getByRole("link", { name: ticker, exact: true }) });
    await expect(missingPriceRow).toContainText("No price");
    await expect(missingPriceRow).toContainText("Not available");
  } finally {
    try {
      if (snapshotId !== undefined) await backendData(page, `/portfolio-snapshots/${snapshotId}`, { method: "DELETE" });
    } finally {
      try {
        for (const id of transactionIds.reverse()) await backendData(page, `/portfolio-transactions/${id}`, { method: "DELETE" });
      } finally {
        for (const resource of ["portfolio-holdings", "portfolio-cash-balances"]) {
          for (const row of await backendData<Array<{id:number}>>(page, `/${resource}?portfolio_id=${portfolio.id}`)) {
            await backendData(page, `/${resource}/${row.id}`, {method:"DELETE"});
          }
        }
        await backendData(page, `/portfolios/${portfolio.id}`, {method:"DELETE"});
      }
    }
  }
});
