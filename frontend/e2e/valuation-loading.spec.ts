import { expect, test } from "@playwright/test";
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
      await expect(page.getByRole("main").getByText("Loading industry allocations...", { exact: true })).toBeVisible();
    } finally {
      release();
      await page.unrouteAll({ behavior: "wait" });
    }
    await expect(page.getByRole("main").getByRole("heading", { name: "Revenue-Weighted Industry Mix", exact: true })).toBeVisible();
  });
}
