import path from "node:path";

import { expect, test } from "@playwright/test";

import { backendData, createCompany, signIn } from "./helpers";

const PDF_FIXTURE = path.resolve(
  process.cwd(),
  "..",
  "backend",
  "tests",
  "fixtures",
  "financial_statement_table.pdf",
);

test("PDF upload, candidate review, promotion, and reconciliation", async ({ page }) => {
  await signIn(page);
  const unique = Date.now().toString().slice(-7);
  const company = await createCompany(page, {
    ticker: `P${unique}`,
    local_symbol: `P${unique}`,
    name: "PDF E2E Fixture",
    market: "IN",
    primary_exchange: "NSE",
    country: "India",
    currency: "INR",
  });

  await page.goto(`/companies/${company.id}/filings`);
  const uploadPanel = page
    .getByRole("heading", { name: "Upload PDF Filing" })
    .locator("..")
    .locator("..");
  await uploadPanel.getByLabel("PDF filing").setInputFiles(PDF_FIXTURE);
  await uploadPanel.getByLabel("Title", { exact: true }).fill("Mock Integration Financial Statements");
  await uploadPanel.getByLabel("Published date").fill("2026-05-31");
  await uploadPanel.getByRole("button", { name: "Upload PDF" }).click();
  await expect(uploadPanel.getByRole("status")).toContainText("1 pages, 1 tables, 12 candidates");

  await page.getByRole("link", { name: "Financials" }).click();
  await expect(page.getByRole("heading", { name: "Extracted Financial Candidates" })).toBeVisible();
  await expect(page.getByText("There are 12 extraction candidates")).toBeVisible();

  while (await page.getByRole("button", { name: "Accept" }).count()) {
    const acceptButtons = page.getByRole("button", { name: "Accept" });
    const reviewedStatuses = page.getByText("reviewed", { exact: true });
    const reviewedBefore = await reviewedStatuses.count();
    await acceptButtons.first().click();
    await expect(reviewedStatuses).toHaveCount(reviewedBefore + 1);
  }

  while (await page.getByRole("button", { name: "Add unit" }).count()) {
    const addUnitButtons = page.getByRole("button", { name: "Add unit" });
    const overriddenStatuses = page.getByText("overridden", { exact: true });
    const overriddenBefore = await overriddenStatuses.count();
    await addUnitButtons.first().click();
    await page.getByLabel("Reporting unit").fill("million shares");
    await page.getByRole("button", { name: "Save" }).click();
    await expect(overriddenStatuses).toHaveCount(overriddenBefore + 1);
  }

  await expect(page.getByRole("heading", { name: "Review Required" })).toHaveCount(0);
  await page.getByRole("button", { name: "Promote Reviewed Candidates" }).click();
  await expect(page.getByRole("status")).toContainText("Successfully promoted 12 candidates");
  await expect(page.getByText("No extracted candidates yet")).toBeVisible();
  await expect(page.getByText("2 of 2 periods normalized")).toBeVisible();
  await expect(page.getByText(/exact matches, 0 mismatches/)).toBeVisible();

  const coverage = await backendData<{
    status: string;
    normalized_period_count: number;
    trust_ready_period_count: number;
  }>(
    page,
    `/api/companies/${company.id}/financial-statements/normalized/coverage`,
  );
  expect(coverage.status).toBe("complete");
  expect(coverage.normalized_period_count).toBe(2);
  expect(coverage.trust_ready_period_count).toBe(2);
});
