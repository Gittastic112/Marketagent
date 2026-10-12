import { expect, test } from "@playwright/test";
import { backendData, createCompany, signIn } from "./helpers";

test("India manual source is review-only, retry-safe and usable on mobile", async ({ page }) => {
  await signIn(page);
  const symbol = `M${Date.now().toString().slice(-7)}`;
  const company = await createCompany(page, { ticker: symbol, local_symbol: symbol,
    name: "Mock Data manual filing", market: "IN", primary_exchange: "NSE", currency: "INR", country: "India" });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`/companies/${company.id}/filings`);
  const content = page.getByRole("main");
  await expect(content.getByText("India Manual Filings", { exact: true })).toBeVisible();
  const panel = content.getByRole("heading", { name: "Add Manual Filing" }).locator("../..");
  const title = "Mock Data FY2026 source";
  for (let attempt = 0; attempt < 2; attempt++) {
    await panel.getByLabel("Title", { exact: true }).fill(title);
    await panel.getByLabel("Source URL").fill("https://example.com/report.pdf#page=14");
    await panel.getByLabel("Published date").fill("2026-05-31");
    await panel.getByLabel("Source text for review").fill("Mock Data revenue 100, requires review.");
    const saved = page.waitForResponse(response => response.request().method() === "POST"
      && new URL(response.url()).pathname === `/companies/${company.id}/filings`);
    await panel.getByRole("button", { name: "Add filing source" }).click();
    expect((await saved).ok()).toBeTruthy();
    await expect(content.getByRole("cell").filter({ hasText: title })).toHaveCount(1);
    await expect(content.getByRole("link", { name: "Open source", exact: true })).toHaveAttribute("href", "https://example.com/report.pdf#page=14");
  }
  const filings = await backendData<Array<{ id: number }>>(page, `/api/companies/${company.id}/filings`);
  expect(filings).toHaveLength(1);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  const coverage = await backendData<{ normalized_period_count: number }>(page,
    `/api/companies/${company.id}/financial-statements/normalized/coverage`);
  expect(coverage.normalized_period_count).toBe(0);
});
