import { expect, test, type Page, type TestInfo } from "@playwright/test";

import { signIn } from "./helpers";


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

async function collectTypographyFailures(page: Page): Promise<string[]> {
  return page.evaluate(() => {
    const failures: string[] = [];
    const visible = (element: HTMLElement) => {
      const style = window.getComputedStyle(element);
      return style.display !== "none" && style.visibility !== "hidden" && element.getClientRects().length > 0;
    };
    const fontSize = (element: Element) => Number.parseFloat(window.getComputedStyle(element).fontSize);
    const bodySize = fontSize(document.body);
    if (bodySize < 15) failures.push(`Body text is ${bodySize}px; expected at least 15px`);

    const title = document.querySelector<HTMLElement>("main h1");
    if (title) {
      const titleSize = fontSize(title);
      if (titleSize < 26 || titleSize > 40) {
        failures.push(`Page title is ${titleSize}px; expected 26–40px`);
      }
    }

    for (const heading of document.querySelectorAll<HTMLElement>(".panel-header h2")) {
      if (visible(heading) && fontSize(heading) < 16) {
        failures.push(`Panel heading is ${fontSize(heading)}px: ${heading.textContent?.trim()}`);
      }
    }

    const undersized = [...document.querySelectorAll<HTMLElement>(
      "main p, main span, main td, main th, main label, main button, main a",
    )].filter((element) => (
      visible(element)
      && !element.classList.contains("sr-only")
      && Boolean(element.textContent?.trim())
      && fontSize(element) < 12
    ));
    for (const element of undersized.slice(0, 5)) {
      failures.push(`Text is ${fontSize(element)}px: ${element.textContent?.trim().slice(0, 80)}`);
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
    { message: `${label} must finish applying its React server stream`, timeout: 30_000 },
  ).toBe(0);
  await expect(page.getByText(/Internal Server Error|Application error|API request failed: 5\d\d/i)).toHaveCount(0);

  const overflow = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  expect(overflow.scrollWidth, `${label} must not overflow horizontally`).toBeLessThanOrEqual(
    overflow.clientWidth + 1,
  );
  expect(await collectSemanticFailures(page), `${label} semantic failures`).toEqual([]);
  expect(await collectTypographyFailures(page), `${label} typography failures`).toEqual([]);

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
