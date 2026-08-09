import { expect, test, type Page, type TestInfo } from "@playwright/test";

import { signIn } from "./helpers";


const CORE_ROUTES = [
  ["dashboard", "/"],
  ["companies", "/companies"],
  ["portfolio", "/portfolio"],
  ["valuation", "/valuation"],
  ["documents", "/documents"],
  ["data-health", "/data-health"],
] as const;

async function collectSemanticFailures(page: Page): Promise<string[]> {
  return page.evaluate(() => {
    const failures: string[] = [];
    const ids = [...document.querySelectorAll<HTMLElement>("[id]")].map((element) => element.id);
    const duplicates = [...new Set(ids.filter((id, index) => ids.indexOf(id) !== index))];
    if (duplicates.length) failures.push(`Duplicate IDs: ${duplicates.join(", ")}`);

    const visible = (element: HTMLElement) => {
      const style = window.getComputedStyle(element);
      return style.display !== "none" && style.visibility !== "hidden" && element.getClientRects().length > 0;
    };
    const hasName = (element: HTMLElement) => {
      const labelledBy = element.getAttribute("aria-labelledby");
      const labelledText = labelledBy
        ? labelledBy.split(/\s+/).map((id) => document.getElementById(id)?.textContent || "").join(" ")
        : "";
      return Boolean(
        element.getAttribute("aria-label")?.trim()
        || element.getAttribute("title")?.trim()
        || labelledText.trim()
        || element.textContent?.trim(),
      );
    };

    for (const element of document.querySelectorAll<HTMLElement>("button, a[href]")) {
      if (visible(element) && !hasName(element)) {
        failures.push(`Unnamed ${element.tagName.toLowerCase()}: ${element.outerHTML.slice(0, 160)}`);
      }
    }
    for (const input of document.querySelectorAll<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>(
      "input:not([type=hidden]), select, textarea",
    )) {
      if (
        visible(input)
        && input.labels?.length === 0
        && !input.getAttribute("aria-label")
        && !input.getAttribute("aria-labelledby")
      ) {
        failures.push(`Unlabelled form control: ${input.outerHTML.slice(0, 160)}`);
      }
    }
    for (const image of document.querySelectorAll<HTMLImageElement>("img")) {
      if (!image.hasAttribute("alt")) failures.push(`Image missing alt: ${image.src}`);
    }
    return failures;
  });
}

async function verifyRoute(
  page: Page,
  testInfo: TestInfo,
  label: string,
  path: string,
  viewport: { width: number; height: number },
) {
  await page.setViewportSize(viewport);
  await page.goto(path);
  await expect(page.locator("main")).toBeVisible();
  await expect.poll(() => page.evaluate(() => document.fonts.status)).toBe("loaded");
  await expect.poll(
    () => page.locator('body > div[hidden][id^="S:"]').count(),
    { message: `${label} must finish applying its React server stream` },
  ).toBe(0);

  const overflow = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  expect(overflow.scrollWidth, `${label} must not overflow horizontally`).toBeLessThanOrEqual(
    overflow.clientWidth + 1,
  );
  expect(await collectSemanticFailures(page), `${label} semantic failures`).toEqual([]);

  await page.keyboard.press("Tab");
  await expect.poll(() => page.evaluate(() => document.activeElement?.tagName)).not.toBe("BODY");
  await page.screenshot({
    path: testInfo.outputPath(`${label}-${viewport.width}.png`),
    fullPage: true,
    animations: "disabled",
  });
}

test("core routes pass semantic, keyboard, overflow, and responsive screenshot gates", async ({ page }, testInfo) => {
  await signIn(page);
  for (const [label, path] of CORE_ROUTES) {
    await verifyRoute(page, testInfo, label, path, { width: 1440, height: 900 });
    await verifyRoute(page, testInfo, label, path, { width: 390, height: 844 });
  }
});

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
