import { readFileSync } from "node:fs";
import path from "node:path";
import { expect, test } from "@playwright/test";
import { backendData, createCompany, signIn } from "./helpers";
import type { FinancialExtractionCandidate } from "../lib/api/financials";

test("financial review rejects stale evidence, preserves corrections and promotes only inspected versions", async ({page}) => {
  await signIn(page);
  const suffix = Date.now().toString().slice(-7);
  const company = await createCompany(page, {ticker: `FR${suffix}`, local_symbol: `FR${suffix}`,
    name: "Mock Data candidate recovery", market: "IN", primary_exchange: "NSE", country: "India", currency: "INR"});
  const upload = await page.request.post(`/api/backend/api/companies/${company.id}/filings/pdf`, {
    headers: {origin: new URL(page.url()).origin}, multipart: {document_type: "annual_report",
      title: "Mock Data candidate review versions", published_at: "2026-05-31T00:00:00Z",
      file: {name: "mock-financial-review.pdf", mimeType: "application/pdf", buffer: readFileSync(
        path.resolve(process.cwd(), "..", "backend", "tests", "fixtures", "financial_statement_table.pdf"))}}});
  expect(upload.ok()).toBe(true);
  const candidates = await backendData<FinancialExtractionCandidate[]>(page, `/api/companies/${company.id}/financial-statements/extracted`);
  const candidate = candidates.find(item => item.metric_code === "revenue" && item.unit)!;
  expect(candidate).toBeTruthy();
  await page.goto(`/companies/${company.id}/fundamentals`);
  const grid = page.getByRole("region", {name: "Extracted financial candidates", exact: true});
  const row = grid.getByRole("row").filter({has: page.getByRole("cell", {name: String(candidate.fiscal_year), exact: true})})
    .filter({hasText: "revenue"}).first();
  const changed = await backendData<FinancialExtractionCandidate>(page, `/api/financial-line-items/${candidate.id}/override`, {
    method: "PATCH", data: {value: 12500, unit: candidate.unit, expected_updated_at: candidate.updated_at}});
  await row.getByRole("button", {name: "Accept", exact: true}).click();
  await expect(page.getByRole("alert").filter({hasText: "Candidate changed since it was loaded"})).toBeVisible();
  await page.getByRole("button", {name: "Reload candidates (discard unsaved correction)"}).click();
  await expect(row).toContainText("12,500");
  await row.getByRole("button", {name: "Undo", exact: true}).click();
  await row.getByRole("button", {name: "Reject", exact: true}).click();
  await expect(row).toContainText("rejected");
  await expect(page.getByRole("button", {name: "Promote Reviewed Candidates"})).toBeDisabled();
  await row.getByRole("button", {name: "Undo", exact: true}).click();
  await row.getByRole("button", {name: "Override", exact: true}).click();
  await row.getByLabel("Corrected value").fill("12000");
  await row.getByLabel("Reporting unit").fill(candidate.unit!);
  let fail = true;
  await page.route(`**/api/backend/api/financial-line-items/${candidate.id}/override`, route => fail
    ? route.fulfill({status: 503, json: {errors: [{message: "Mock Data correction temporarily unavailable"}]}}) : route.continue());
  await row.getByRole("button", {name: "Save", exact: true}).click();
  await expect(page.getByRole("alert").filter({hasText: "Mock Data correction temporarily unavailable"})).toBeVisible();
  await expect(row.getByLabel("Corrected value")).toHaveValue("12000");
  await expect(row.getByLabel("Reporting unit")).toHaveValue(candidate.unit!);
  fail = false;
  await row.getByRole("button", {name: "Save", exact: true}).click();
  await expect(row).toContainText("overridden");
  const latest = await backendData<FinancialExtractionCandidate>(page, `/api/financial-line-items/${candidate.id}`);
  expect(latest.value).toBe(12000);
  expect(latest.updated_at).not.toBe(changed.updated_at);
  await backendData(page, `/api/financial-line-items/${candidate.id}/override`, {method: "PATCH",
    data: {value: 13000, unit: candidate.unit, expected_updated_at: latest.updated_at}});
  await page.getByRole("button", {name: "Promote Reviewed Candidates"}).click();
  await expect(page.getByRole("alert").filter({hasText: "Reviewed candidates changed"})).toBeVisible();
  expect(await backendData<unknown[]>(page, `/companies/${company.id}/financial-periods`)).toHaveLength(0);
  await page.getByRole("button", {name: "Reload candidates (discard unsaved correction)"}).click();
  await expect(row).toContainText("13,000");
  await page.getByRole("button", {name: "Promote Reviewed Candidates"}).click();
  await expect(page.getByRole("status").filter({hasText: "Successfully promoted 1 candidates."})).toBeVisible();
  const periods = await backendData<Array<{metrics: Array<{metric_name: string; value: number}>}>>(
    page, `/companies/${company.id}/financial-periods`);
  expect(periods).toHaveLength(1);
  expect(periods[0].metrics).toEqual(expect.arrayContaining([expect.objectContaining({metric_name: "revenue", value: 13000})]));
  await page.reload();
  const plan = page.getByRole("region", {name: "Financial review plan", exact: true});
  await expect(plan.getByText("Source linked", {exact: true})).toBeVisible();
  await plan.getByLabel("Review track", {exact: true}).selectOption("bank_equity");
  await plan.getByRole("button", {name: "Update review plan", exact: true}).click();
  await expect(plan.getByRole("columnheader", {name: "Input", exact: true}).first()).toBeVisible();
  await expect(plan.getByRole("rowheader", {name: "Book equity", exact: true}).first()).toBeVisible();
  await expect(plan.getByRole("rowheader", {name: "Debt", exact: true})).toHaveCount(0);
  expect(await backendData(page, `/companies/${company.id}/financial-periods`)).toEqual(periods);
  await page.setViewportSize({width: 390, height: 844});
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  await page.screenshot({path: test.info().outputPath("financial-review-recovery-mobile.png"), fullPage: true});
});
