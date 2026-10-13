import { expect, test, type Locator, type Page, type TestInfo } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

import { backendData, createCompany, signIn } from "./helpers";

async function reachWithTab(page: Page, region: Locator) {
  for (let attempt = 0; attempt < 80; attempt++) {
    if (await region.evaluate(element => element === document.activeElement)) break;
    await page.keyboard.press("Tab");
  }
  await expect(region).toBeFocused();
}

async function checkAccessibility(page: Page, testInfo: TestInfo, label: string) {
  const result = await new AxeBuilder({page})
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
    .analyze();
  await testInfo.attach(`${label}-accessibility`, {
    body: JSON.stringify({violations: result.violations, incomplete: result.incomplete,
      passedRuleIds: result.passes.map(rule => rule.id)}, null, 2),
    contentType: "application/json",
  });
  expect(result.violations).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
}

test("populated macro observations and thesis assumptions are reachable and scrollable with the keyboard", async ({page}, testInfo) => {
  await signIn(page);
  const suffix = Date.now().toString().slice(-6);
  const seriesName = `Mock Data keyboard scroll ${suffix}`;
  const series = await backendData<{id: number}>(page, "/macro", {
    method: "POST",
    data: {name: seriesName, units: "Synthetic index points", frequency: "Daily",
      description: "Mock Data for keyboard-scroll verification. These observations are synthetic, not provider evidence."},
  });
  // Enough real persisted fixture rows to exceed the 192px observation viewport.
  // These APIs are local manual intake; no FRED import or AI request is made.
  for (let day = 1; day <= 12; day++) {
    await backendData(page, `/macro/${series.id}/observations`, {
      method: "POST", data: {date_recorded: `2026-09-${String(day).padStart(2, "0")}`, value: 100 + day},
    });
  }

  const company = await createCompany(page, {ticker: `MS${suffix}`, local_symbol: `MS${suffix}`,
    name: "Mock Data keyboard scroll company"});
  const thesis = await backendData<{id: number}>(page, "/thesis-notes", {
    method: "POST", data: {company_id: company.id, title: "Mock Data scrollable thesis",
      thesis_text: "Mock Data synthetic assumptions for keyboard and accessibility checks only.", status: "active"},
  });
  for (let index = 1; index <= 4; index++) {
    await backendData(page, `/thesis-notes/${thesis.id}/assumptions`, {
      method: "POST", data: {thesis_note_id: thesis.id,
        description: `Mock Data assumption ${index}: synthetic operating evidence remains unreviewed and requires an independent source before financial use.`,
        original_confidence: "medium", current_confidence: "medium"},
    });
  }

  for (const width of [1440, 390]) {
    await page.setViewportSize({width, height: 900});
    await page.goto("/macro?tab=series");
    const observations = page.getByRole("main").getByRole("region", {name: `${seriesName} observations`, exact: true});
    await expect(observations).toBeVisible();
    await expect(observations.locator("tbody tr")).toHaveCount(12);
    expect(await observations.evaluate(element => element.scrollHeight > element.clientHeight)).toBe(true);
    await reachWithTab(page, observations);
    const beforeDown = await observations.evaluate(element => element.scrollTop);
    await page.keyboard.press("ArrowDown");
    await expect.poll(() => observations.evaluate(element => element.scrollTop)).toBeGreaterThan(beforeDown);
    await expect(observations).toBeFocused();
    await checkAccessibility(page, testInfo, `macro-populated-${width}`);
    await page.screenshot({path: testInfo.outputPath(`macro-populated-${width}.png`), fullPage: true});

    await page.goto(`/companies/${company.id}/thesis`);
    const assumptions = page.getByRole("main").getByRole("region", {name: "Thesis assumptions", exact: true});
    await expect(assumptions).toBeVisible();
    await expect(assumptions.locator("tbody tr")).toHaveCount(4);
    await expect(assumptions).toContainText("Mock Data assumption 1");
    await reachWithTab(page, assumptions);
    const scrollsHorizontally = await assumptions.evaluate(element => element.scrollWidth > element.clientWidth);
    // Desktop may fit all six columns; the populated mobile table must overflow.
    if (width === 390) expect(scrollsHorizontally).toBe(true);
    if (scrollsHorizontally) {
      const beforeRight = await assumptions.evaluate(element => element.scrollLeft);
      await page.keyboard.press("ArrowRight");
      await expect.poll(() => assumptions.evaluate(element => element.scrollLeft)).toBeGreaterThan(beforeRight);
      await expect(assumptions).toBeFocused();
    }
    await checkAccessibility(page, testInfo, `thesis-populated-${width}`);
    await page.screenshot({path: testInfo.outputPath(`thesis-populated-${width}.png`), fullPage: true});
  }
});
