import { expect, test, type Page } from "@playwright/test";
import { readFile, writeFile } from "node:fs/promises";
import AxeBuilder from "@axe-core/playwright";
import { backendData, createCompany, signIn } from "./helpers";
import type { DcfAssumptionSet } from "../lib/api/valuation";

async function createSavedModel(page: Page) {
  const company = await createCompany(page, { ticker: `AI${Date.now().toString().slice(-7)}`,
    local_symbol: `AI${Date.now().toString().slice(-7)}`, name: "Mock Data explanation workflow" });
  const model = await backendData<{id: number}>(page, `/companies/${company.id}/valuation-models`, {
    method: "POST", data: {company_id: company.id, name: "Mock Data saved explanation", model_type: "fcff_dcf"} });
  const row = await backendData<{id: number; updated_at: string}>(page, `/valuation-models/${model.id}/assumptions`, {
    method: "POST", data: {scenario: "Base", story_text: "Mock Data saved story", projection_years_count: 5,
      starting_revenue: 1000, current_operating_margin: 0.2, target_operating_margin: 0.22, tax_rate: 0.25,
      revenue_growth_years_json: {1: 0.05, 2: 0.05, 3: 0.05, 4: 0.05, 5: 0.05},
      sales_to_capital_ratio: 2.5, starting_invested_capital: 600, wacc_start: 0.1, wacc_terminal: 0.09,
      terminal_growth_rate: 0.02, terminal_roic: 0.12, cash: 0, debt: 0, diluted_shares: 10,
      net_income: 100, book_value_of_equity: 500, cash_flow_currency: "USD", discount_rate_currency: "USD"} });
  return {company, model, row, path: `/companies/${company.id}/valuation/${model.id}`};
}

function evidence(modelId: number, row: {id: number; updated_at: string}) {
  return {assumption_set_id: row.id, assumptions_updated_at: row.updated_at, valuation_model_id: modelId,
    scenario: "Base", output_id: 1, output_calculated_at: row.updated_at, currency: "USD",
    ai_output_id: 1, claim_type: "AI Interpretation", is_current: true, basis_verified: true,
    provider_name: "mock", model_name: "Mock Data browser fixture", prompt_version: "mock-workflow-v1",
    input_hash: "a".repeat(64), source_ids: [`valuation:${modelId}`, `dcf_assumption_set:${row.id}`],
    generated_at: row.updated_at, review_status: "pending", is_mock: true,
    confidence_label: "not_evaluated", limitations: "Mock Data transport fixture; no AI provider was called.",
    interpretation_quality: "not_evaluated"};
}

async function checkState(page: Page, label: string) {
  const result = await new AxeBuilder({page}).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]).analyze();
  await writeFile(test.info().outputPath(`${label}-accessibility.json`), JSON.stringify(result, null, 2));
  expect(result.violations.map(v => ({rule: v.id, nodes: v.nodes.map(n => ({target: n.target, reason: n.failureSummary}))}))).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  await page.screenshot({path: test.info().outputPath(`${label}.png`), fullPage: true});
}

test("AI failure and analysis controls do not submit or erase unsaved valuation inputs", async ({page}) => {
  await signIn(page);
  const {model, path} = await createSavedModel(page);
  await page.goto(path);
  const sections = page.getByRole("navigation", {name: "Valuation model sections"});
  await sections.getByRole("button", {name: "Thesis & Story", exact: true}).click();
  await page.locator("#story_text:visible").fill("Mock Data unsaved story must survive");
  await page.locator("main #advanced-dcf-form").evaluate(form => {
    form.setAttribute("data-observed-submits", "0");
    form.addEventListener("submit", () => form.setAttribute("data-observed-submits", String(Number(form.getAttribute("data-observed-submits")) + 1)));
  });
  let accidentalSaves = 0;
  page.on("request", request => {
    if (request.method() === "POST" && new URL(request.url()).pathname === path) accidentalSaves++;
  });
  await page.route("**/api/backend/valuation/*/scenarios/*/ai/memo", route => route.request().method() === "POST"
    ? route.fulfill({status: 503, json: {errors: [{message: "Mock Data provider unavailable"}]}}) : route.continue());
  await sections.getByRole("button", {name: "Valuation Memo", exact: true}).click();
  await page.getByRole("checkbox", {name: /external AI provider/}).check();
  await page.getByRole("button", {name: "Generate Memo", exact: true}).click();
  await expect(page.getByRole("main").getByText("Mock Data provider unavailable", {exact: true})).toBeVisible();
  await sections.getByRole("button", {name: "Macro Sensitivity", exact: true}).click();
  await page.getByRole("button", {name: "Top-Down (Regression)", exact: true}).click();
  await page.getByRole("button", {name: "Bottom-Up (Segments)", exact: true}).click();
  await expect(page.locator("main #advanced-dcf-form")).toHaveAttribute("data-observed-submits", "0");
  expect(accidentalSaves).toBe(0);
  await sections.getByRole("button", {name: "Thesis & Story", exact: true}).click();
  await expect(page.locator("#story_text:visible")).toHaveValue("Mock Data unsaved story must survive");
  expect(await backendData<unknown[]>(page, `/valuation-models/${model.id}/assumptions`)).toHaveLength(1);
});

test("late narrative suggestions cannot replace edits and copying estimates requires review and explicit save", async ({page}) => {
  await signIn(page);
  const {model, row, path} = await createSavedModel(page);
  let release!: () => void;
  const held = new Promise<void>(resolve => { release = resolve; });
  let began!: () => void;
  const started = new Promise<void>(resolve => { began = resolve; });
  let mapped = 0;
  await page.route("**/api/backend/valuation/*/scenarios/*/ai/narrative-to-numbers", async route => {
    const input = route.request().postDataJSON();
    expect(input.assumption_set_id).toBe(row.id);
    expect(input.assumptions_updated_at).toBe(row.updated_at);
    mapped++;
    const old = input.narrative_text.includes("obsolete");
    if (old) { began(); await held; }
    await route.fulfill({json: {data: {target_operating_margin: old ? 0.8 : 0.24,
      target_operating_margin_reason: old ? "Mock Data obsolete interpretation" : "Mock Data revised interpretation",
      revenue_growth_years: {1: 0.1, 2: 0.08, 3: 0.06, 4: 0.05, 5: 0.04}, revenue_growth_reason: "Mock Data growth",
      sales_to_capital_ratio: 2.5, sales_to_capital_reason: "Mock Data reinvestment",
      terminal_growth_rate: 0.02, terminal_growth_reason: "Mock Data terminal", evidence: evidence(model.id, row)},
      meta: {is_mock: true}, errors: []}});
  });
  await page.goto(path);
  const sections = page.getByRole("navigation", {name: "Valuation model sections"});
  await sections.getByRole("button", {name: "Narrative to Numbers", exact: true}).click();
  const panel = page.getByRole("region", {name: "Narrative estimates", exact: true});
  await panel.getByLabel("Narrative for AI estimates").fill("Mock Data obsolete narrative");
  await panel.getByRole("checkbox", {name: /external AI provider/}).check();
  await panel.getByRole("button", {name: "Map to Assumptions", exact: true}).click();
  await started;
  await panel.getByLabel("Narrative for AI estimates").fill("Mock Data revised story to save");
  await panel.getByRole("button", {name: "Map to Assumptions", exact: true}).click();
  await expect(panel.getByText(/Mock Data revised interpretation/)).toBeVisible();
  release();
  await expect(panel.getByText(/Mock Data obsolete interpretation/)).toHaveCount(0);
  await expect(panel.getByRole("button", {name: "Copy reviewed estimates to form"})).toBeDisabled();
  await panel.getByRole("checkbox", {name: /I reviewed these estimates/}).check();
  await panel.getByRole("button", {name: "Copy reviewed estimates to form"}).click();
  await expect(page.getByRole("main").getByText(/Reviewed AI estimates were copied to unsaved fields/)).toBeVisible();
  expect(await backendData<unknown[]>(page, `/valuation-models/${model.id}/assumptions`)).toHaveLength(1);
  await sections.getByRole("button", {name: "Operating Margins", exact: true}).click();
  await expect(page.locator("#target_operating_margin:visible")).toHaveValue("0.24");

  let releaseSave!: () => void;
  const heldSave = new Promise<void>(resolve => { releaseSave = resolve; });
  let saved!: () => void;
  const savedResponse = new Promise<void>(resolve => { saved = resolve; });
  await page.route(`**${path}`, async route => {
    if (route.request().method() !== "POST") return route.continue();
    const response = await route.fetch();
    saved(); await heldSave;
    await route.fulfill({response});
  });
  await page.getByRole("button", {name: "Save & Run Valuation"}).click();
  await savedResponse;
  await expect(page.locator("#target_operating_margin:visible")).toBeDisabled();
  releaseSave();
  await expect(page.getByRole("main").getByText("Assumptions saved and valuation recalculated.")).toBeVisible();
  await expect(page.locator("#target_operating_margin:visible")).toHaveValue("0.24");
  const versions = await backendData<DcfAssumptionSet[]>(
    page, `/valuation-models/${model.id}/assumptions`);
  expect(versions).toHaveLength(2);
  expect(versions[0].story_text).toBe("Mock Data revised story to save");
  expect(versions[0].target_operating_margin).toBe(0.24);
  expect(versions[1].id).toBe(row.id);
  expect(mapped).toBe(2);

  const latest = versions[0];
  await sections.getByRole("button", {name: "Sensitivity Tables", exact: true}).click();
  await expect(page.locator(".sensitivity-card:visible")).toHaveCount(6);
  expect(latest.sensitivity_tables).toHaveLength(6);
  expect(latest.sensitivity_tables!.map(table => table.table_type).sort()).toEqual([
    "beta_vs_equity_risk_premium", "debt_ratio_vs_cost_of_debt",
    "revenue_growth_vs_target_margin", "sales_to_capital_vs_margin",
    "terminal_roc_vs_terminal_growth", "wacc_vs_terminal_growth",
  ]);
  for (const table of latest.sensitivity_tables ?? []) {
    if (["beta_vs_equity_risk_premium", "debt_ratio_vs_cost_of_debt"].includes(table.table_type)) {
      expect(table.x_axis_json.values).toEqual([]);
      expect(table.y_axis_json.values).toEqual([]);
      expect(table.values_json).toEqual({});
      expect(table.x_axis_json.unavailable_reason).toContain("MISSING_FUNDING_INPUT");
      const card = page.locator(".sensitivity-card:visible").filter({has: page.getByRole("heading", {
        name: `${table.y_axis_json.name} vs ${table.x_axis_json.name}`, exact: true,
      })});
      await expect(card.getByText(`Not available: ${table.x_axis_json.unavailable_reason}`, {exact: true})).toBeVisible();
      continue;
    }
    expect(table.x_axis_json.values).toHaveLength(5);
    expect(table.y_axis_json.values).toHaveLength(5);
    const x = Number(table.x_axis_json.values[2].toFixed(4));
    const y = Number(table.y_axis_json.values[2].toFixed(4));
    const values = table.values_json as Record<string, Record<string, number | null>>;
    const center = Object.entries(Object.entries(values).find(([key]) => Number(key) === y)![1])
      .find(([key]) => Number(key) === x)![1];
    expect(center).toBeCloseTo(latest.outputs!.intrinsic_value_per_share!, 8);
  }
  await sections.getByRole("button", {name: "Reverse DCF", exact: true}).click();
  const reverse = page.getByRole("region", {name: "Reverse DCF analysis"});
  await reverse.getByLabel(/^Comparison price/).fill(String(latest.outputs!.intrinsic_value_per_share));
  const reversed = page.waitForResponse(response => response.url().endsWith("/api/backend/dcf/reverse"));
  await reverse.getByRole("button", {name: "Solve Reverse DCF"}).click();
  const reverseData = (await (await reversed).json()).data;
  expect(reverseData.assumption_set_id).toBe(latest.id);
  expect(reverseData.converged).toBe(true);
  expect(Math.abs(reverseData.price_residual)).toBeLessThanOrEqual(0.01);
  await expect(reverse.getByText(/Calculated price:/)).toBeVisible();
  await page.route("**/api/backend/valuation/*/scenarios/*/ai/memo*", async route => {
    if (route.request().method() === "GET") return route.continue();
    const basis = route.request().postDataJSON();
    expect(basis.assumption_set_id).toBe(latest.id);
    expect(basis.assumptions_updated_at).toBe(latest.updated_at);
    await route.fulfill({json: {data: {memo_markdown: "Mock Data explanation of the reviewed saved story", is_mock: true,
      evidence: evidence(model.id, latest)}, meta: {is_mock: true}, errors: []}});
  });
  await sections.getByRole("button", {name: "Valuation Memo", exact: true}).click();
  const memo = page.getByRole("region", {name: "Valuation memo", exact: true});
  await memo.getByRole("checkbox", {name: /external AI provider/}).check();
  await memo.getByRole("button", {name: "Generate Memo", exact: true}).click();
  await expect(memo.getByText("Mock Data explanation of the reviewed saved story", {exact: true})).toBeVisible();
  expect(await backendData<unknown[]>(page, `/valuation-models/${model.id}/assumptions`)).toHaveLength(2);
});

for (const width of [1440, 390]) {
  test(`memo pending, failure, retry and safe evidence export at ${width}px`, async ({page}) => {
    await signIn(page);
    const {model, row, path} = await createSavedModel(page);
    let release!: () => void;
    const held = new Promise<void>(resolve => { release = resolve; });
    let began!: () => void;
    const started = new Promise<void>(resolve => { began = resolve; });
    let reads = 0;
    const memoText = "Mock Data memo\n<script>window.untrustedMemoExecuted = true</script>\nSaved assumptions are uncertain.";
    await page.route("**/api/backend/valuation/*/scenarios/*/ai/memo*", async route => {
      expect(route.request().method()).toBe("GET");
      expect(new URL(route.request().url()).searchParams.get("assumption_set_id")).toBe(String(row.id));
      if (++reads === 1) {
        began(); await held;
        return route.fulfill({status: 503, json: {errors: [{message: "Mock Data stored memo unavailable"}]}});
      }
      await route.fulfill({json: {data: {memo_markdown: memoText, is_mock: true, evidence: evidence(model.id, row)}, meta: {is_mock: true}, errors: []}});
    });
    await page.setViewportSize({width, height: 1000});
    await page.goto(path);
    const sections = page.getByRole("navigation", {name: "Valuation model sections"});
    if (width === 390) await sections.getByRole("combobox", {name: /^Section/}).selectOption("valuation_memo");
    else await sections.getByRole("button", {name: "Valuation Memo", exact: true}).click();
    const panel = page.getByRole("region", {name: "Valuation memo", exact: true});
    await started;
    await expect(panel.getByText("Loading stored memo…", {exact: true})).toBeVisible();
    await checkState(page, `memo-loading-${width}`);
    release();
    await expect(panel.getByRole("alert")).toContainText("Mock Data stored memo unavailable");
    await expect(panel.getByText(/No memo generated/)).toHaveCount(0);
    await checkState(page, `memo-error-${width}`);
    await panel.getByRole("button", {name: "Reload stored memo"}).click();
    await expect(panel.getByText(/Review: pending/)).toBeVisible();
    await expect(panel.getByText(memoText, {exact: true})).toBeVisible();
    expect(await page.evaluate(() => "untrustedMemoExecuted" in window)).toBe(false);
    await checkState(page, `memo-success-${width}`);
    const downloadReady = page.waitForEvent("download");
    await panel.getByRole("button", {name: "Download memo with evidence"}).click();
    const download = await downloadReady;
    const downloadPath = test.info().outputPath(download.suggestedFilename());
    await download.saveAs(downloadPath);
    const exported = await readFile(downloadPath, "utf8");
    expect(exported).toContain('"review_status": "pending"');
    expect(exported).toContain(`"assumption_set_id": ${row.id}`);
    expect(exported).toContain(memoText);
    expect(await backendData<unknown[]>(page, `/valuation-models/${model.id}/assumptions`)).toHaveLength(1);
  });
}
