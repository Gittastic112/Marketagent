import { expect, test } from "@playwright/test";
import { backendData, createCompany, signIn } from "./helpers";

test("private research finds older sources, preserves filters after saves, and opens evidence", async ({ page }) => {
  await signIn(page);
  const company = await createCompany(page, { ticker: "LIBRARY", local_symbol: "LIBRARY", name: "Mock Data source library" });
  const other = await createCompany(page, { ticker: "LIBOTHER", local_symbol: "LIBOTHER", name: "Mock Data other company" });
  const originalText = "Mock Data: Original historical passage about currency headwinds and future uncertainty.";
  const sources: Array<{ id: number }> = [];
  for (let index = 0; index < 23; index++) {
    sources.push(await backendData(page, "/brief-sources", { method: "POST", data: {
      company_id: company.id, title: `Mock Data library source ${index}`,
      text: index === 0 ? originalText : `Mock Data: Original source ${index} contains a distinct passage for pagination verification.`,
    } }));
  }
  let scans = 0;
  page.on("request", request => { if (/brief-sources\/\d+\/analyze/.test(request.url())) scans++; });
  await page.goto("/daily-brief");
  await page.locator("summary").filter({hasText: "Add or browse private research sources"}).click();
  const library = page.getByRole("region", { name: "Saved research sources" });
  await library.getByLabel("Filter by company").selectOption(String(company.id));
  await library.getByRole("button", { name: "Search sources", exact: true }).click();
  await expect(library.locator(".brief-source-card")).toHaveCount(20);
  await expect(library.getByText("Mock Data library source 0", { exact: true })).toHaveCount(0);
  await library.getByRole("button", { name: "Older sources" }).click();
  await expect(library.locator(".brief-source-card")).toHaveCount(3);
  await expect(library.getByRole("button", { name: "Older sources" })).toBeDisabled();
  await library.getByRole("button", { name: "Previous page" }).click();
  await expect(library.locator(".brief-source-card")).toHaveCount(20);

  await library.getByLabel("Search saved sources").fill("currency headwinds");
  await library.getByLabel("Source format").selectOption("text");
  await library.getByLabel("Scan status").selectOption("not_scanned");
  await library.getByRole("button", { name: "Search sources", exact: true }).click();
  await expect(library.locator(".brief-source-card")).toHaveCount(1);
  await expect(library.getByRole("button", { name: "Previous page" })).toBeDisabled();
  await expect(library.getByRole("link", { name: "Inspect source text", exact: true })).toHaveAttribute("href", `/daily-brief/sources/${sources[0].id}`);
  await expect(library.getByRole("button", { name: "Scan with AI" })).toBeDisabled();

  // An intake save outside the current filters must not be prepended to matches.
  await page.getByLabel(/^Company/).selectOption(String(other.id));
  await page.getByLabel("Source title", { exact: true }).fill("Mock Data saved outside filters");
  await page.getByLabel("Source text", { exact: true }).fill("Mock Data: A separate company's original source text with unrelated research context.");
  await page.getByRole("button", { name: "Save source privately" }).click();
  await expect(page.getByRole("link", { name: "Inspect saved source: Mock Data saved outside filters" })).toBeVisible();
  await expect(library.locator(".brief-source-card")).toHaveCount(1);
  await expect(library.getByText("Mock Data saved outside filters", { exact: true })).toHaveCount(0);
  await library.getByRole("link", { name: "Inspect source text", exact: true }).click();
  await expect(page.locator(".brief-source-text")).toHaveText(originalText);
  expect(scans).toBe(0);
});

test("search failures clear old results and late replies cannot replace a newer search", async ({ page }) => {
  await signIn(page);
  await page.goto("/daily-brief");
  await page.locator("summary").filter({hasText: "Add or browse private research sources"}).click();
  const library = page.getByRole("region", { name: "Saved research sources" });
  let releaseSlow!: () => void;
  const slow = new Promise<void>(resolve => { releaseSlow = resolve; });
  let markStarted!: () => void;
  const started = new Promise<void>(resolve => { markStarted = resolve; });
  await page.route("**/api/backend/brief-sources/search*", async route => {
    const q = new URL(route.request().url()).searchParams.get("q");
    if (q === "slow") { markStarted(); await slow; }
    if (q === "failure") return route.fulfill({ status: 503, json: { errors: [{ message: "Search temporarily unavailable" }] } });
    return route.fulfill({ json: { data: { items: [], next_before_id: q === "slow" ? 99 : null }, meta: {}, errors: [] } });
  });
  try {
    await library.getByLabel("Search saved sources").fill("slow");
    await library.getByRole("button", { name: "Search sources", exact: true }).click();
    await started;
    await library.getByLabel("Search saved sources").fill("failure");
    await library.getByRole("button", { name: "Search sources", exact: true }).click();
    await expect(library.getByRole("alert")).toContainText("Search temporarily unavailable");
    await expect(library.locator(".brief-source-card")).toHaveCount(0);
    const slowResponse = page.waitForResponse(response => new URL(response.url()).searchParams.get("q") === "slow");
    releaseSlow();
    await slowResponse;
    await expect(library.getByRole("alert")).toContainText("Search temporarily unavailable");
    await expect(library.getByRole("button", { name: "Older sources" })).toBeDisabled();
    await library.getByLabel("Search saved sources").fill("no matches");
    await library.getByRole("button", { name: "Search sources", exact: true }).click();
    await expect(library.getByText(/No sources match these filters/)).toBeVisible();
    await expect(library.getByRole("alert")).toHaveCount(0);
  } finally { releaseSlow(); }
});

test("mobile source retrieval remains usable when the company catalog fails", async ({ page }, testInfo) => {
  await signIn(page);
  const company = await createCompany(page, { ticker: "LIBMOBILE", local_symbol: "LIBMOBILE", name: "Mock Data mobile library" });
  await backendData(page, "/brief-sources", { method: "POST", data: {
    company_id: company.id, title: "Mock Data mobile source",
    text: "Mock Data: Original source text remains searchable when company catalog loading fails.",
  } });
  await page.route("**/api/backend/companies", route => route.fulfill({ status: 503,
    json: { errors: [{ message: "Company catalog temporarily unavailable" }] } }));
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/daily-brief");
  await page.locator("summary").filter({hasText: "Add or browse private research sources"}).click();
  await expect(page.getByRole("alert").filter({ hasText: "Company catalog temporarily unavailable" })).toBeVisible();
  const library = page.getByRole("region", { name: "Saved research sources" });
  await library.getByLabel("Search saved sources").fill("Mock Data mobile source");
  await library.getByRole("button", { name: "Search sources", exact: true }).click();
  await expect(library.locator(".brief-source-card")).toHaveCount(1);
  await expect(library.getByLabel("Filter by company")).toBeDisabled();
  await expect(page.getByRole("button", { name: "Save source privately" })).toBeDisabled();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1)).toBe(true);
  await library.screenshot({ path: testInfo.outputPath("mobile-source-search.png") });
});
