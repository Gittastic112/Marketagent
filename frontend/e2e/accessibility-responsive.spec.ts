import { expect, test } from "@playwright/test";

import { backendData, signIn } from "./helpers";
import { verifyRoutes } from "./route-checks";


const CORE_ROUTES = [
  ["dashboard", "/"],
  ["daily-brief", "/daily-brief"],
  ["alerts", "/alerts"],
  ["portfolio", "/portfolio"],
  ["portfolio-manage", "/portfolio/manage"],
  ["market-regime", "/portfolio/regime"],
  ["companies", "/companies"],
  ["research", "/research"],
  ["narratives", "/narratives"],
  ["events", "/events"],
  ["contradictions", "/intelligence/review"],
  ["macro", "/macro"],
  ["valuation", "/valuation"],
  ["documents", "/documents"],
  ["ingestion", "/data"],
  ["data-health", "/data-health"],
  ["sources", "/sources"],
  ["admin", "/admin/damodaran"],
  ["settings", "/settings"],
  ["search", "/search"],
  ["thesis-notes", "/thesis-notes"],
  ["evaluations", "/evaluations"],
  ["research-sessions", "/research/sessions"],
  ["social", "/social"],
  ["quick-valuation", "/valuation/quick"],
  ["source-comparison", "/daily-brief/triage"],
  ["market-prices", "/market-prices"],
  ["sign-in", "/auth/signin"],
] as const;

for (const viewport of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
  test(`core routes at ${viewport.width}px pass semantic, keyboard, overflow, and screenshot gates`, async ({ page }, testInfo) => {
    // The aggregate audit includes axe and screenshots for 28 pages. Each page
    // still has the unchanged 15-second readiness budget in verifyRoutes.
    test.setTimeout(180_000);
    await signIn(page);
    await verifyRoutes(page, testInfo, CORE_ROUTES, viewport, "Isolated Mock Data browser seed");
  });
}

test("mobile navigation exposes and restores keyboard focus", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await signIn(page);
  const trigger = page.getByRole("button", { name: "Open navigation" });
  await trigger.focus();
  await trigger.press("Enter");
  await expect(page.getByRole("navigation", { name: "Primary navigation" })).toBeVisible();
  await page.getByRole("button", { name: "Close navigation panel" }).press("Enter");
  await expect(page.getByRole("navigation", { name: "Primary navigation" })).not.toBeVisible();
  await expect(trigger).toBeFocused();

  await trigger.press("Enter");
  await page.keyboard.press("Escape");
  await expect(page.getByRole("navigation", { name: "Primary navigation" })).not.toBeVisible();
  await expect(trigger).toBeFocused();
});

test("a mobile table can be reached and scrolled with the keyboard", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await signIn(page);
  await page.goto("/data");
  const region = page.getByRole("main").locator(".table-wrap");
  await expect(region).toBeVisible();
  expect(await region.evaluate(element => element.scrollWidth > element.clientWidth)).toBe(true);
  for (let attempt = 0; attempt < 40 && !await region.evaluate(element => element === document.activeElement); attempt++) {
    await page.keyboard.press("Tab");
  }
  await expect(region).toBeFocused();
  await page.keyboard.press("ArrowRight");
  await expect.poll(() => region.evaluate(element => element.scrollLeft)).toBeGreaterThan(0);
});

test("mobile decision fields remain inside their panels and can be edited", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await signIn(page);
  const companies = await backendData<Array<{ id: number; ticker: string }>>(page, "/companies");
  const company = companies.find(row => row.ticker === "E2EUSD");
  expect(company).toBeTruthy();
  await page.goto(`/companies/${company!.id}/decisions`);
  const content = page.getByRole("main");
  await expect(content.getByLabel("New Evidence", { exact: true })).toBeVisible();
  const fields = content.locator("input:not([type=hidden]), textarea, select, button[type=submit]");
  for (const field of await fields.all()) {
    if (!await field.isVisible()) continue;
    await field.scrollIntoViewIfNeeded();
    const bounds = await field.evaluate(element => {
      const field = element.getBoundingClientRect();
      const panel = element.closest(".panel")!.getBoundingClientRect();
      return { left:field.left, right:field.right, panelLeft:panel.left, panelRight:panel.right,
        width:innerWidth, label:element.getAttribute("name") || element.textContent };
    });
    expect(bounds.left, `${bounds.label} left edge`).toBeGreaterThanOrEqual(Math.max(0, bounds.panelLeft));
    expect(bounds.right, `${bounds.label} right edge`).toBeLessThanOrEqual(Math.min(bounds.width, bounds.panelRight));
  }
  await content.getByLabel("New Evidence", { exact: true }).fill("Mock Data: editable mobile evidence field.");
  await content.getByLabel(/^Price at Time/).fill("0");
  await content.getByLabel("Rationale", { exact: true }).fill("Mock Data: keyboard entry stays visible.");
  await expect(content.getByLabel(/^Price at Time/)).toHaveValue("0");
  await page.screenshot({ path:testInfo.outputPath("mobile-decision-fields.png"), fullPage:true });
});

test("mobile intake forms keep readable controls inside their cards", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await signIn(page);
  for (const route of ["/portfolio/manage", "/sources", "/data", "/alerts", "/events", "/thesis-notes"]) {
    await page.goto(route);
    const fields = page.getByRole("main").locator(".form-grid input:not([type=hidden]):not([type=checkbox]), .form-grid select, .form-grid textarea, .form-grid button[type=submit]");
    await expect(fields.first()).toBeVisible();
    let checked = 0;
    for (const field of await fields.all()) {
      if (!await field.isVisible()) continue;
      const bounds = await field.evaluate(element => {
        const control = element.getBoundingClientRect();
        const card = element.closest(".panel")!.getBoundingClientRect();
        return { left:control.left, right:control.right, width:control.width, button:element.tagName === "BUTTON", textFits:element.scrollWidth <= element.clientWidth,
          cardLeft:card.left, cardRight:card.right, name:element.getAttribute("name") || element.textContent };
      });
      if (!bounds.button) expect(bounds.width, `${route}: ${bounds.name} readable width`).toBeGreaterThanOrEqual(200);
      expect(bounds.textFits, `${route}: ${bounds.name} content fits`).toBe(true);
      expect(bounds.left, `${route}: ${bounds.name} left`).toBeGreaterThanOrEqual(Math.max(0, bounds.cardLeft));
      expect(bounds.right, `${route}: ${bounds.name} right`).toBeLessThanOrEqual(Math.min(390, bounds.cardRight));
      checked++;
    }
    expect(checked, `${route} contains visible intake controls`).toBeGreaterThan(0);
    await page.screenshot({path:testInfo.outputPath(`${route.slice(1).replaceAll("/", "-")}-forms-390.png`), fullPage:true});
  }
  await page.goto("/portfolio/regime");
  const submit = page.getByRole("button", {name:"Submit Metric", exact:true});
  await expect(submit).toBeVisible();
  expect(await submit.evaluate(element => getComputedStyle(element).backgroundColor)).not.toBe("rgba(0, 0, 0, 0)");
  await page.screenshot({path:testInfo.outputPath("regime-form-390.png"), fullPage:true});
});
