import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { backendData, signIn } from "./helpers";
import { verifyRoutes } from "./route-checks";

for (const width of [1440, 390]) {
  test(`valuation industry loading remains accessible at ${width}px`, async ({ page }, testInfo) => {
    await signIn(page);
    const companies = await backendData<Array<{ id: number; ticker: string }>>(page, "/companies");
    const company = companies.find(row => row.ticker === "E2EUSD");
    expect(company).toBeTruthy();

    // Keep the real loading state visible throughout the audit, regardless of
    // machine speed. Release the request afterward and verify recovery.
    let release!: () => void;
    const pending = new Promise<void>(resolve => { release = resolve; });
    await page.route(`**/api/backend/companies/${company!.id}/industry-allocations`, async route => {
      await pending;
      await route.continue();
    });
    try {
      await verifyRoutes(page, testInfo, [["valuation-industry-loading", `/companies/${company!.id}/valuation`]],
        { width, height: 900 }, "Isolated Mock Data with a pending industry-allocation request");
      await page.getByRole("main").getByText("Industry and benchmark settings", {exact: true}).click();
      await expect(page.getByRole("main").getByText("Loading industry allocations...", { exact: true })).toBeVisible();
      const audit = await new AxeBuilder({page}).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]).analyze();
      await testInfo.attach("expanded-industry-loading-accessibility", {body: JSON.stringify(audit), contentType: "application/json"});
      expect(audit.violations).toEqual([]);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
      await page.screenshot({path: testInfo.outputPath(`expanded-industry-loading-${width}.png`), fullPage: true});
    } finally {
      release();
      await page.unrouteAll({ behavior: "wait" });
    }
    await expect(page.getByRole("main").getByRole("heading", { name: "Revenue-Weighted Industry Mix", exact: true })).toBeVisible();
  });
}

for (const manual of [false, true]) {
  test(`Mock Data source refresh displays the adopted growth schedule (manual=${manual})`, async ({page}) => {
    const {createCompany, expandDraftSections} = await import("./helpers");
    await signIn(page);
    const company = await createCompany(page, {ticker: `G${Date.now().toString().slice(-7)}`, name: "Mock Data growth refresh"});
    await page.goto(`/companies/${company.id}/valuation/draft`);
    await page.getByRole("button", {name: "Create draft", exact: true}).click();
    await expandDraftSections(page);
    const growth = {"1": manual ? 0.123 : 0.087, "2": 0.04};
    if (manual) await page.locator("#revenue-growth:visible").fill(JSON.stringify(growth));
    const draft = await backendData<{id: number}>(page, `/companies/${company.id}/valuation-drafts/current`);
    await page.route(`**/api/backend/valuation-drafts/${draft.id}`, async route => {
      if (route.request().method() !== "GET") return route.continue();
      const response = await route.fetch();
      const body = await response.json();
      body.data.assumptions_json.revenue_growth_years_json = growth;
      await route.fulfill({response, json: body});
    });
    await page.route(`**/api/backend/companies/${company.id}/valuation-source-refresh`, async route => {
      if (route.request().method() !== "POST") return route.continue();
      await route.fulfill({json: {data: {id: 9999, company_id: company.id, status: "success", started_at: "2026-11-16T00:00:00Z",
        finished_at: "2026-11-16T00:00:01Z", scheduled_for: null, steps: [], warnings: ["Mock Data refresh response"], draft_ids: [draft.id]}, errors: []}});
    });
    await page.getByRole("button", {name: "Fetch latest source inputs"}).click();
    await expect(page.getByText("Source refresh finished.", {exact: false})).toBeVisible();
    await expect(page.locator("#revenue-growth:visible")).toHaveValue(JSON.stringify(growth, null, 2));
    expect(JSON.parse(await page.locator('#revenue-growth').evaluate((element: HTMLTextAreaElement) => String(new FormData(element.form!).get('revenue_growth_years_json'))))).toEqual(growth);
  });
}
