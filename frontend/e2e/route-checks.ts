import { writeFile } from "node:fs/promises";
import { readdirSync } from "node:fs";
import path from "node:path";
import { expect, type Page, type TestInfo } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

export const ROUTE_READY_BUDGET_MS = 15_000;

const pageRoutes = readdirSync(path.join(process.cwd(), "app"), {recursive: true})
  .map(String).filter(file => file === "page.tsx" || file.endsWith("/page.tsx"))
  .map(file => new RegExp("^/" + file.replace(/(^|\/)page\.tsx$/, "").split("/")
    .filter(Boolean).map(segment => segment.startsWith("[") ? "[^/]+" : segment.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("/") + "/?$"));

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
    if (innerWidth <= 600) {
      for (const control of document.querySelectorAll<HTMLElement>(".button-row > a, .button-row > button")) {
        if (!visible(control) || control.closest(".table-wrap")) continue;
        const bounds = control.getBoundingClientRect();
        const row = control.parentElement!.getBoundingClientRect();
        if (bounds.left < Math.max(0, row.left) - 1 || bounds.right > Math.min(innerWidth, row.right) + 1) {
          failures.push(`Clipped mobile action: ${control.textContent?.trim()}`);
        }
      }
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

export async function verifyRoute(
  page: Page,
  testInfo: TestInfo,
  label: string,
  path: string,
  viewport: { width: number; height: number },
) {
  await page.setViewportSize(viewport);
  const routeStartedAt = Date.now();
  await page.goto(path);
  await expect(page.locator("main")).toBeVisible();
  await expect.poll(() => page.evaluate(() => document.fonts.status)).toBe("loaded");
  await expect.poll(
    () => page.locator('body > div[hidden][id^="S:"]').count(),
    { message: `${label} must finish applying its React server stream`, timeout: 30_000 },
  ).toBe(0);
  if (path === "/auth/signin") {
    // This client Suspense boundary can show an empty main before hydration.
    // Require the usable form within the same route budget before keyboard checks.
    await expect(page.getByLabel("Username", { exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Sign in", exact: true })).toBeEnabled();
  }
  const routeReadyMs = Date.now() - routeStartedAt;
  expect(
    routeReadyMs,
    `${label} must render within the route-ready budget`,
  ).toBeLessThanOrEqual(ROUTE_READY_BUDGET_MS);
  await expect(page.getByText(/Internal Server Error|Application error|API request failed: 5\d\d/i)).toHaveCount(0);
  await expect(page.getByRole("heading", { name: /This workspace could not be loaded|This page could not be found/i })).toHaveCount(0);
  await expect(page.getByText(/Authentication error|authentication is not configured|local session is missing or expired/i)).toHaveCount(0);

  const overflow = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
  }));
  expect(overflow.scrollWidth, `${label} must not overflow horizontally`).toBeLessThanOrEqual(
    overflow.clientWidth + 1,
  );
  expect(await collectSemanticFailures(page), `${label} semantic failures`).toEqual([]);
  expect(await collectTypographyFailures(page), `${label} typography failures`).toEqual([]);

  const accessibility = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
    .analyze();
  const accessibilityPath = testInfo.outputPath(`${label}-${viewport.width}-accessibility.json`);
  await writeFile(accessibilityPath, JSON.stringify({
    engine: accessibility.testEngine,
    violations: accessibility.violations,
    incomplete: accessibility.incomplete,
    passed_rules: accessibility.passes.map(rule => rule.id),
  }, null, 2));
  await testInfo.attach(`${label}-${viewport.width}-accessibility`, {
    path: accessibilityPath, contentType: "application/json",
  });
  expect(accessibility.violations.map(violation => ({
    rule: violation.id, impact: violation.impact,
    targets: violation.nodes.map(node => ({ target: node.target, reason: node.failureSummary })),
  })), `${label} automatically detectable accessibility failures`).toEqual([]);

  const internalLinks = await page.locator("main a[href]").evaluateAll(links => links.map(link => ({
    text: link.textContent?.trim(), href: link.getAttribute("href") || "",
  })).filter(link => link.href.startsWith("/") && !link.href.startsWith("//")));
  const unknownPageLinks = internalLinks.filter(link => {
    const pathname = new URL(link.href, "http://local.invalid").pathname;
    return !pathname.startsWith("/api/") && !pageRoutes.some(route => route.test(pathname));
  });
  expect(unknownPageLinks, `${label} must link to implemented page routes`).toEqual([]);

  await page.keyboard.press("Tab");
  await expect.poll(() => page.evaluate(() => document.activeElement?.tagName)).not.toBe("BODY");
  await page.screenshot({
    path: testInfo.outputPath(`${label}-${viewport.width}.png`),
    fullPage: true,
    animations: "disabled",
  });
  return { label, path, viewport, route_ready_ms: routeReadyMs, overflow,
    accessibility_passed_rules: accessibility.passes.length,
    accessibility_incomplete_rules: accessibility.incomplete.length,
    controls: await page.locator("main button, main input, main select, main textarea").count(), internal_links: internalLinks };
}

export async function verifyRoutes(page: Page, testInfo: TestInfo,
  routes: ReadonlyArray<readonly [string, string]>, viewport: { width: number; height: number }, dataset: string) {
  const measurements = [];
  const failures = [];
  try {
    for (const [label, url] of routes) {
      try {
        measurements.push(await verifyRoute(page, testInfo, label, url, viewport));
      } catch (error) {
        failures.push({ label, url, error: error instanceof Error ? error.message : String(error) });
        await page.screenshot({ path: testInfo.outputPath(`${label}-${viewport.width}-failed.png`), fullPage: true }).catch(() => {});
      }
    }
  } finally {
    const measurementPath = testInfo.outputPath("route-measurements.json");
    await writeFile(measurementPath, JSON.stringify({ dataset, budget_ms: ROUTE_READY_BUDGET_MS, measurements, failures }, null, 2));
    await testInfo.attach("route-measurements", { path: measurementPath, contentType: "application/json" });
  }
  expect(failures, "Every route must pass; all failures are retained for a single repair pass").toEqual([]);
}
