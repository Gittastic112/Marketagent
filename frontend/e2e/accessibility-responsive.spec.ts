import { expect, test } from "@playwright/test";

import { signIn } from "./helpers";
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
