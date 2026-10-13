import { expect, test } from "@playwright/test";

import { backendData, createCompany, signIn } from "./helpers";


test("company setup creates an authenticated company with an industry mapping", async ({ page }) => {
  await signIn(page);
  const unique = Date.now().toString().slice(-7);
  const ticker = `C${unique}`;
  await page.goto("/companies");
  await page.getByRole("link", { name: "Add company", exact: true }).click();
  const wizard = page
    .getByRole("heading", { name: "Company Setup Wizard" })
    .locator("xpath=..");

  await wizard.locator("#ticker:visible").fill(ticker);
  await wizard.getByRole("button", { name: "Next Step" }).click();
  await wizard.getByRole("button", { name: "Skip Lookup" }).click();
  await wizard.locator("#name:visible").fill("Company Setup E2E Fixture");
  await wizard.getByRole("button", { name: "Next Step" }).click();

  const industry = wizard.locator("#damodaran_industry:visible");
  await expect(industry).toBeEnabled();
  expect(await industry.locator("option").count()).toBeGreaterThan(1);
  await industry.selectOption({ label: "Software (System & Application)" });
  await wizard.getByRole("button", { name: "Next Step" }).click();
  await expect(wizard.getByRole("heading", { name: "Step 5: Review & Create" })).toBeVisible();
  await wizard.getByRole("button", { name: "Create Company" }).click();

  await expect(page).toHaveURL(/\/companies\/\d+$/);
  await expect(page.getByRole("heading", { level: 1, name: `${ticker} Company Setup E2E Fixture`, exact: true })).toBeVisible();
  const companies = await backendData<Array<{ ticker: string; damodaran_industry: string | null }>>(page, "/companies");
  expect(companies).toContainEqual(expect.objectContaining({
    ticker,
    damodaran_industry: "Software (System & Application)",
  }));
});


test("revenue-weighted industry mix persists weights and source provenance", async ({ page }) => {
  await signIn(page);
  const unique = Date.now().toString().slice(-7);
  const company = await createCompany(page, {
    ticker: `I${unique}`,
    local_symbol: `I${unique}`,
    name: "Industry Mix E2E Fixture",
  });
  const source = await backendData<{ id: number }>(page, "/sources", {
    method: "POST",
    data: { name: `Industry Mix Filing ${unique}`, source_type: "regulatory_filing" },
  });
  const document = await backendData<{ id: number; title: string }>(page, "/raw-documents", {
    method: "POST",
    data: {
      company_id: company.id,
      source_id: source.id,
      document_type: "annual_report",
      title: `Segment Revenue Note ${unique}`,
      published_at: "2026-07-31T00:00:00Z",
      raw_text: "Software revenue 60%; semiconductor revenue 40%.",
      content_hash: `industry-mix-${unique}`,
    },
  });

  await page.goto(`/companies/${company.id}/valuation`);
  const mix = page.locator("section.industry-mix-card");
  await expect(mix.getByRole("heading", { name: "Revenue-Weighted Industry Mix" })).toBeVisible();
  await mix.getByLabel("Segment name").fill("Software");
  await mix.getByLabel("Industry for Software").selectOption({ label: "Software (System & Application)" });
  await mix.getByLabel("Revenue weight for Software").fill("60");
  await mix.getByRole("button", { name: "Add segment" }).click();

  const segmentInputs = mix.getByLabel("Segment name");
  await segmentInputs.nth(1).fill("Semiconductors");
  await mix.getByLabel("Industry for Semiconductors").selectOption({ label: "Semiconductor" });
  await mix.getByLabel("Revenue weight for Semiconductors").fill("40");
  await mix.getByLabel("Weight source").selectOption({ label: document.title });
  await mix.getByLabel("As-of date").fill("2026-07-31");
  await mix.getByLabel("Basis note").fill("User-reviewed segment revenue disclosure.");
  await mix.getByRole("button", { name: "Save mix" }).click();

  await expect(mix.getByText("Saved as User Assumption")).toBeVisible();
  await expect(mix.getByText("partial benchmark coverage")).toBeVisible();
  await expect(mix.getByText(`Source: ${document.title}`)).toBeVisible();
  const stored = await backendData<{
    source_document_id: number | null;
    total_weight_percent: number;
    allocations: Array<{ segment_name: string; weight_percent: number }>;
  }>(page, `/companies/${company.id}/industry-allocations`);
  expect(stored.source_document_id).toBe(document.id);
  expect(stored.total_weight_percent).toBe(100);
  expect(stored.allocations).toEqual([
    expect.objectContaining({ segment_name: "Software", weight_percent: 60 }),
    expect.objectContaining({ segment_name: "Semiconductors", weight_percent: 40 }),
  ]);

  await page.reload();
  await expect(mix.getByLabel("Revenue weight for Software")).toHaveValue("60");
  await expect(mix.getByLabel("Revenue weight for Semiconductors")).toHaveValue("40");
});


test("company tabs and grouped navigation remain usable on mobile", async ({ page }) => {
  await signIn(page);
  const unique = Date.now().toString().slice(-7);
  const company = await createCompany(page, {
    ticker: `N${unique}`,
    local_symbol: `N${unique}`,
    name: "Navigation E2E Fixture",
  });

  await page.goto(`/companies/${company.id}`);
  const companyNavigation = page.getByRole("navigation", { name: "Company workspace" });
  await expect(companyNavigation.getByRole("link", { name: "Overview" })).toHaveAttribute(
    "aria-current",
    "page",
  );
  await companyNavigation.getByRole("link", { name: "Filings" }).click();
  await expect(page).toHaveURL(`/companies/${company.id}/filings`);
  await expect(companyNavigation.getByRole("link", { name: "Filings" })).toHaveAttribute(
    "aria-current",
    "page",
  );

  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "Open navigation" }).click();
  const primaryNavigation = page.getByRole("navigation", { name: "Primary navigation" });
  await expect(primaryNavigation.getByText("Today", { exact: true })).toBeVisible();
  await expect(primaryNavigation.getByRole("link", { name: "Research", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Close navigation panel" }).click();
});


test("research discloses AI transmission and renders provider failure inline", async ({ page }) => {
  await signIn(page);
  await page.goto("/research/sessions");
  await page.getByRole("button", { name: "Start New Session" }).click();
  await expect(page).toHaveURL(/\/research\/sessions\/\d+$/);

  const input = page.getByPlaceholder("Ask about companies, events, or market trends...");
  await input.fill("Summarize the evidence in this empty research session.");
  await expect(page.getByRole("button", { name: "Send" })).toBeDisabled();
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Send" }).click();

  await expect(page.locator("p.inline-error[role=alert]")).toContainText("AI is not configured");
  await expect(page.getByText(/Your research message was saved/)).toBeVisible();
  await expect(
    page.getByText("Summarize the evidence in this empty research session.", { exact: true }),
  ).toBeVisible();
});


test("CSV preview preserves row-level recovery details and blocks apply", async ({ page }) => {
  await signIn(page);
  await page.goto("/market-prices");
  const importer = page.getByRole("heading", { name: "Import Market Prices" }).locator("xpath=ancestor::section[1]");
  await importer.locator('input[type="file"]').setInputFiles({
    name: "invalid-market-prices.csv",
    mimeType: "text/csv",
    buffer: Buffer.from(
      "ticker,price,currency,as_of_date\nBAD,not-a-number,US,not-a-date\n",
    ),
  });
  await importer.getByRole("button", { name: "Preview Import" }).click();

  await expect(importer.getByText("Row Errors", { exact: true })).toBeVisible();
  await expect(importer.getByText(/Invalid decimal/)).toBeVisible();
  await expect(importer.getByRole("button", { name: "Confirm Import" })).toHaveCount(0);
  await expect(importer.locator('input[type="file"]')).toHaveValue(/invalid-market-prices\.csv$/);
});


test("CSV market prices preview, apply, and export without losing the imported row", async ({ page }) => {
  await signIn(page);
  const ticker = `P${Date.now().toString().slice(-7)}`;
  await page.goto("/market-prices");
  const importer = page.getByRole("heading", { name: "Import Market Prices" }).locator("xpath=ancestor::section[1]");
  await importer.locator('input[type="file"]').setInputFiles({
    name: "valid-market-prices.csv",
    mimeType: "text/csv",
    buffer: Buffer.from(`ticker,price,currency,as_of_date\n${ticker},123.45,USD,2026-07-31\n`),
  });
  await importer.getByRole("button", { name: "Preview Import" }).click();

  await expect(importer.getByText("Valid: 1", { exact: true })).toBeVisible();
  await expect(importer.getByText("Errors: 0", { exact: true })).toBeVisible();
  await importer.getByRole("button", { name: "Confirm Import" }).click();
  await expect(importer.getByText("Successfully imported 1 records.", { exact: true })).toBeVisible();
  const prices = await backendData<Array<{ ticker: string; price: number }>>(page, "/market-prices");
  expect(prices).toContainEqual(expect.objectContaining({ ticker, price: 123.45 }));

  await page.goto(`/market-prices?ticker=${encodeURIComponent(ticker)}`);
  const importedRow = page.getByRole("row").filter({ hasText: ticker });
  await expect(importedRow).toHaveCount(1);
  await expect(importedRow.getByText("Manual entry", { exact: true })).toBeVisible();

  await page.goto("/settings");
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("link", { name: "Export Market Prices" }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe("market_prices.csv");
  const stream = await download.createReadStream();
  let exported = "";
  for await (const chunk of stream) exported += chunk.toString();
  expect(exported).toContain(ticker);
});


test("SEC readiness blocks ineligible companies and failed ingestion is recoverable in Data Health", async ({ page }) => {
  await signIn(page);
  const unique = Date.now().toString().slice(-7);
  const company = await createCompany(page, {
    ticker: `S${unique}`,
    local_symbol: `S${unique}`,
    name: "SEC Readiness E2E Fixture",
    cik: null,
  });
  await page.goto("/data");
  const secCompany = page.locator("#sec-fetch-company-id:visible");
  await expect(secCompany).toBeDisabled();
  await expect(secCompany).toHaveValue("");
  await expect(page.getByRole("button", { name: "Fetch recent SEC filings" })).toBeDisabled();
  await expect(secCompany.locator("option")).toHaveText(["Select company with CIK"]);

  const source = await backendData<{ id: number }>(page, "/sources", {
    method: "POST",
    data: {
      name: `Blocked RSS ${unique}`,
      source_type: "rss",
      base_url: "http://127.0.0.1/private-feed.xml",
      active: true,
    },
  });
  const result = await backendData<{ error_count: number; errors: string[] }>(page, "/ingest/rss-feed", {
    method: "POST",
    data: {
      source_id: source.id,
      company_id: company.id,
      feed_url: "http://127.0.0.1/private-feed.xml",
    },
  });
  expect(result.error_count).toBe(1);
  expect(result.errors).toEqual(["RSS provider could not fetch the feed."]);

  await page.goto("/data-health");
  await expect(page.getByText("rss_ingestion", { exact: true }).last()).toBeVisible();
  await expect(page.locator("tbody tr").filter({ hasText: "rss_ingestion" }).last()).toContainText("failed");
});
