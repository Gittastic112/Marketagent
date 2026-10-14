import path from "node:path";

import { expect, test } from "@playwright/test";

import { backendData, createCompany, expandDraftSections, signIn } from "./helpers";
import type { NormalizedSnapshotRead } from "../lib/api/financials";
import type { ValuationSetupDraft } from "../lib/api/valuation-drafts";

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
  await expect(uploadPanel.getByRole("status")).toContainText("1 of 1 pages scanned, 1 tables, 12 candidates");

  await page.getByRole("link", { name: "Financials" }).click();
  const candidateHeading = page.getByRole("heading", { name: "Extracted Financial Candidates", exact: true });
  await expect(candidateHeading).toBeVisible();
  const candidateReview = candidateHeading.locator("xpath=../../..");
  await expect(page.getByRole("main").getByText("There are 12 extraction candidates")).toBeVisible();

  while (await page.getByRole("button", { name: "Accept" }).count()) {
    const acceptButtons = page.getByRole("button", { name: "Accept" });
    const reviewedStatuses = page.getByRole("main").getByText("reviewed", { exact: true });
    const reviewedBefore = await reviewedStatuses.count();
    await acceptButtons.first().click();
    await expect(reviewedStatuses).toHaveCount(reviewedBefore + 1);
  }

  while (await page.getByRole("button", { name: "Add unit" }).count()) {
    const addUnitButtons = page.getByRole("button", { name: "Add unit" });
    const overriddenStatuses = page.getByRole("main").getByText("overridden", { exact: true });
    const overriddenBefore = await overriddenStatuses.count();
    await addUnitButtons.first().click();
    await page.getByLabel("Reporting unit").fill("million shares");
    await page.getByRole("button", { name: "Save" }).click();
    await expect(overriddenStatuses).toHaveCount(overriddenBefore + 1);
  }

  await expect(page.getByRole("heading", { name: "Review Required" })).toHaveCount(0);
  await page.getByRole("button", { name: "Promote Reviewed Candidates" }).click();
  await expect(candidateReview.getByRole("status").filter({ hasText: "Successfully promoted 12 candidates" })).toBeVisible();
  await expect(candidateReview.getByText("No extracted candidates yet")).toBeVisible();
  await expect(page.getByRole("region", { name: "Normalization Coverage" })).toContainText("2 of 2 periods normalized");
  await expect(page.getByRole("region", { name: "Source Reconciliation" })).toContainText(/exact matches, 0 mismatches/);

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

  const snapshots = await backendData<NormalizedSnapshotRead[]>(page,
    `/api/companies/${company.id}/financial-statements/normalized`);
  await page.goto(`/companies/${company.id}/valuation/draft`);
  await expandDraftSections(page);
  await expect(page.locator("#starting_revenue:visible")).toHaveValue("1250");
  const revenueField = page.locator("#starting_revenue:visible").locator("xpath=..");
  await expect(revenueField).toContainText("Normalized Financials");
  await expect(revenueField).toContainText("FY2026");
  await expect(revenueField).toContainText("INR");
  await expect(page.getByRole("button", {name: "Confirm and Create Model"})).toBeDisabled();
  const draft = await backendData<ValuationSetupDraft>(page, `/companies/${company.id}/valuation-drafts`, {method: "POST", data: {}});
  const provenance = draft.provenance_json.starting_revenue;
  expect(typeof provenance).toBe("object");
  if (typeof provenance === "string") throw new Error("Expected structured financial provenance");
  expect(provenance.source_table).toBe("normalized_financial_metrics");
  const snapshot = snapshots.find(item => item.id === provenance.snapshot_id)!;
  const source = snapshot.metrics.find(item => item.id === provenance.source_record_id)!;
  expect(source.metric_code).toBe("revenue");
  expect(source.value).toBe(draft.assumptions_json.starting_revenue);
  expect(provenance.period_id).toBe(snapshot.period_id);
  expect(draft.source_metadata_json.reporting_currency).toBe("INR");
  expect(draft.source_metadata_json.promotion_ready).toBe(false);
  expect(await backendData<unknown[]>(page, `/companies/${company.id}/valuation-models`)).toHaveLength(0);
});
