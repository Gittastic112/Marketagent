import { expect, test, type Page } from "@playwright/test";
import { signIn } from "./helpers";

const meta = { status: "success", source: "Mock Data", is_stale: false, warnings: [], last_updated: "2025-01-02T00:00:00Z" };
const envelope = (data: unknown) => ({ data, meta, errors: [] });
async function openLab(page: Page) {
  await signIn(page);
  await page.route("**/api/backend/companies", route => route.fulfill({ json: envelope([
    { id: 901, ticker: "MOCKA", name: "Mock Data A", market: "US", primary_exchange: "NASDAQ" },
    { id: 902, ticker: "MOCKB", name: "Mock Data B", market: "IN", primary_exchange: "NSE" },
  ]) }));
  await page.goto("/research-lab");
}

for (const width of [1440, 390]) {
  test(`provider choices, changed inputs and failed-attempt link at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await openLab(page);
    await page.locator("summary").filter({ hasText: "Market, identity and calendar adapters" }).click();
    await page.getByLabel("Data action", { exact: true }).selectOption("corporate-actions");
    await expect(page.getByLabel("Explicit provider").locator("option")).toHaveText(["Massive", "Official NSE MCP"]);
    await page.getByLabel("Data action", { exact: true }).selectOption("dated-quote");
    await expect(page.getByLabel("Explicit provider")).toHaveValue("nse_mcp");
    await page.getByLabel("Data action", { exact: true }).selectOption("quote");
    await page.getByLabel("Explicit provider").selectOption("fmp");
    await page.route("**/api/backend/api/data-adapters/fmp/quote", route => route.fulfill({ json: envelope({
      provider: "Mock Data", processing_run_id: 42, observed_at: "2025-01-02T00:00:00Z", warnings: [], source_document_ids: [], result: { price: 12 },
    }) }));
    await page.getByLabel("Ticker or local symbol").fill("MOCKA");
    await page.getByRole("button", { name: "Run market quote", exact: true }).click();
    await expect(page.getByRole("region", { name: "Adapter execution receipt" })).toBeVisible();
    await page.getByLabel("Ticker or local symbol").fill("MOCKB");
    await expect(page.getByRole("region", { name: "Adapter execution receipt" })).toHaveCount(0);
    await page.route("**/api/backend/api/data-adapters/fmp/quote", route => route.fulfill({ status: 503, json: {
      data: null, meta, errors: [{ code: "SOURCE_UNAVAILABLE", message: "Mock Data source unavailable", processing_run_id: 43, retryable: true }],
    } }));
    await page.getByRole("button", { name: "Run market quote", exact: true }).click();
    await expect(page.getByRole("alert").filter({ hasText: "Mock Data source unavailable" })).toContainText("Processing run #43");
    await expect(page.getByRole("link", { name: "Open processing history", exact: true })).toHaveAttribute("href", "/data-health");
  });

  test(`filing drafts stay with their company and candidates have exact links at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await openLab(page);
    await page.locator("summary").filter({ hasText: "Source and document adapters" }).click();
    await page.getByLabel("Source action", { exact: true }).selectOption("india-filings");
    await page.getByLabel("Company for source evidence").selectOption("901");
    await page.getByLabel("Official filing metadata JSON", { exact: true }).fill('[{"title":"Mock Data A"}]');
    await page.getByLabel("Company for source evidence").selectOption("902");
    await expect(page.getByLabel("Official filing metadata JSON", { exact: true })).toHaveValue("");
    await page.getByLabel("Official filing metadata JSON", { exact: true }).fill('[{"title":"Mock Data B"}]');
    await page.getByLabel("Company for source evidence").selectOption("901");
    await expect(page.getByLabel("Official filing metadata JSON", { exact: true })).toHaveValue('[{"title":"Mock Data A"}]');
    await page.getByLabel("Source action", { exact: true }).selectOption("sec-facts");
    await page.route("**/api/backend/api/companies/901/source-adapters/sec-facts", route => route.fulfill({ json: envelope({
      adapter: "Mock Data", processing_run_id: 44, observed_at: "2025-01-02T00:00:00Z", warnings: [], raw_document_ids: [77], candidate_ids: [88],
      status: "success", fetched_count: 1, created_count: 1, duplicate_count: 0, details: {},
    }) }));
    await page.getByRole("button", { name: "Run sec annual facts", exact: true }).click();
    await expect(page.getByRole("link", { name: "Review company candidates" })).toHaveAttribute("href", "/companies/901/fundamentals");
    await page.getByText("Inspect individual candidate evidence", { exact: true }).click();
    await expect(page.getByRole("link", { name: "Inspect candidate #88" })).toHaveAttribute("href", "/documents/77/sections?candidate_id=88");
    await page.getByLabel("Maximum years", { exact: true }).fill("3");
    await expect(page.getByRole("region", { name: "Source candidate review" })).toHaveCount(0);
    await expect(page.getByRole("region", { name: "Adapter execution receipt" })).toHaveCount(0);
  });

  test(`history reaches older runs and displays saved benchmark units at ${width}px`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await openLab(page);
    await page.route("**/api/backend/api/research-lab/runs?*", route => {
      const older = new URL(route.request().url()).searchParams.get("before_run_id");
      return route.fulfill({ json: envelope(older ? [{ run_id: 2, kind: "report", status: "success", created_at: "2025-01-02" },
        { run_id: 1, kind: "report", status: "failed", created_at: "2025-01-01" }] : Array.from({ length: 25 }, (_, i) => ({
          run_id: 100 - i, kind: "report", status: "success", created_at: "2025-01-03",
        }))) });
    });
    await page.route("**/api/backend/api/research-lab/runs/2", route => route.fulfill({ json: envelope({
      run_id: 2, kind: "report", warnings: ["Mock Data"], result: { metrics: { total_return: 0.25 }, benchmark: {
        total_return: 0.125, tracking_error_annualized: 0, beta: 1.2, correlation: null,
      } }, manifest: { adapter: "Mock Data", adapter_version: "1", created_at: "2025-01-02", source_assertion: "user_supplied", knowledge_policy: "unverified", input_sha256: "a".repeat(64), output_sha256: "b".repeat(64) },
    }) }));
    await page.reload();
    await page.locator("summary").filter({ hasText: "Saved research runs" }).click();
    await page.getByRole("button", { name: "Older research runs", exact: true }).click();
    await expect(page.getByRole("link", { name: "Inspect processing history for run 1", exact: true })).toHaveAttribute("href", "/data-health");
    await page.getByRole("button", { name: "Open run 2", exact: true }).click();
    const comparison = page.getByRole("region", { name: "Saved benchmark comparison", exact: true });
    await expect(comparison.getByRole("row", { name: "total return 12.5%", exact: true })).toBeVisible();
    await expect(comparison.getByRole("row", { name: "tracking error annualized 0%", exact: true })).toBeVisible();
    await expect(comparison).toContainText("Unavailable");
    await page.getByRole("button", { name: "Newer research runs", exact: true }).click();
    await expect(page.getByRole("button", { name: "Open run 100", exact: true })).toBeVisible();
    await expect(comparison).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1)).toBe(true);
  });
}
