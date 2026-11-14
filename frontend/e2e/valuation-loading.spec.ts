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
