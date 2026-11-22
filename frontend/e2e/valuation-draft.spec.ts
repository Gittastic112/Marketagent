import { expect, test } from "@playwright/test";

import { backendData, createCompany, expandDraftSections, signIn } from "./helpers";

const ASSUMPTIONS: Record<string, string> = {
  starting_revenue: "1000",
  current_operating_margin: "0.20",
  target_operating_margin: "0.24",
  tax_rate: "0.21",
  sales_to_capital_ratio: "2",
  starting_invested_capital: "500",
  risk_free_rate: "0.04",
  equity_risk_premium: "0.05",
  beta: "1",
  cost_of_equity: "0.09",
  pre_tax_cost_of_debt: "0.05",
  debt_to_capital: "0.20",
  equity_to_capital: "0.80",
  wacc_start: "0.08",
  wacc_terminal: "0.07",
  terminal_growth_rate: "0.03",
  terminal_roic: "0.12",
  cash: "100",
  debt: "50",
  minority_interests: "0",
  preferred_stock: "0",
  employee_options_value: "0",
  diluted_shares: "100",
  current_market_price: "10",
};

test("valuation draft save, reset, refresh, archive, and promotion", async ({ page }) => {
  await signIn(page);
  const unique = Date.now().toString().slice(-7);
  const company = await createCompany(page, {
    ticker: `V${unique}`,
    local_symbol: `V${unique}`,
    name: "Valuation E2E Fixture",
  });

  await page.goto(`/companies/${company.id}/valuation/draft`);
  expect(await backendData(page, `/companies/${company.id}/valuation-drafts/current`)).toBeNull();
  await page.getByRole("button", {name: "Create draft", exact: true}).click();
  await expect(
    page.getByRole("heading", { name: "Review valuation draft: Valuation E2E Fixture" }),
  ).toBeVisible();
  await expandDraftSections(page);

  await page.locator("#starting_revenue:visible").fill("1200");
  let releaseSave!: () => void;
  const pendingSave = new Promise<void>(resolve => { releaseSave = resolve; });
  await page.route("**/api/backend/valuation-drafts/*", async route => {
    if (route.request().method() === "PATCH") await pendingSave;
    await route.continue();
  });
  await page.getByRole("button", { name: "Save Draft" }).click();
  await expect(page.locator("#starting_revenue:visible")).toBeDisabled();
  await expect(page.getByRole("button", {name: "Fetch latest source inputs"})).toBeDisabled();
  await expect(page.getByRole("button", {name: "Confirm and Create Model"})).toBeDisabled();
  releaseSave();
  await expect(page.getByRole("main").getByText("Draft saved")).toBeVisible();
  await expect(page.locator("#starting_revenue:visible")).toBeEnabled();
  await page.unrouteAll({behavior: "wait"});
  await page.getByRole("button", { name: "Reset starting_revenue to source" }).click();
  await expect(page.getByRole("button", { name: "Reset starting_revenue to source" })).toHaveCount(0);

  await page.getByRole("button", { name: "Refresh Stored Inputs" }).click();
  await expect(page.getByRole("heading", { name: "Model Settings" })).toBeVisible();

  await page.getByRole("button", { name: "Archive" }).click();
  await page.getByRole("button", { name: "Confirm archive" }).click();
  await expect(page).toHaveURL(`/companies/${company.id}/valuation`);

  await page.goto(`/companies/${company.id}/valuation/draft`);
  await page.getByRole("button", {name: "Create draft", exact: true}).click();
  await expandDraftSections(page);
  await expect(page.locator("#starting_revenue:visible")).toHaveCount(1);
  for (const [field, value] of Object.entries(ASSUMPTIONS)) {
    await page.locator(`#${field}:visible`).fill(value);
  }
  await page.locator("#revenue-growth:visible").fill(
    JSON.stringify({ 1: 0.10, 2: 0.08, 3: 0.06, 4: 0.05, 5: 0.04 }),
  );

  const reviewCheckboxes = page.locator('input[name="reviewed_field"]');
  const reviewCount = await reviewCheckboxes.count();
  expect(reviewCount).toBeGreaterThan(0);
  for (let index = 0; index < reviewCount; index += 1) {
    await reviewCheckboxes.nth(index).check();
  }
  await expect(page.getByRole("main").getByText("Ready to create")).toBeVisible();

  await page.locator("#model-name:visible").fill(`E2E Reviewed DCF ${unique}`);
  await page.getByLabel("Reason for this first version").fill("Reviewed Mock Data opening assumptions");
  await page.getByRole("button", { name: "Preview first valuation" }).click();
  await page.getByRole("button", { name: "Confirm and Create Model" }).click();
  await expect(page).toHaveURL(new RegExp(`/companies/${company.id}/valuation/\\d+$`));
  await expect(page.getByRole("main").getByText(`E2E Reviewed DCF ${unique}`, { exact: false })).toBeVisible();

  await expect(page.getByRole("main").getByText("User Assumption", { exact: true })).toBeVisible();
  await page.getByRole("main").getByRole("textbox", { name: "Model name", exact: true }).fill(`E2E Updated DCF ${unique}`);
  await page.getByRole("main").getByRole("textbox", { name: "Description", exact: true }).fill("Metadata update from the complete valuation workflow");
  await page.getByRole("button", { name: "Save model details" }).click();
  await expect(page.getByRole("main").getByText(`E2E Updated DCF ${unique}`, { exact: false })).toBeVisible();

  await page.getByRole("navigation", { name: "Valuation model sections" })
    .getByRole("button", { name: "Payouts & Cash Return", exact: true }).click();
  await page.locator("#capex:visible").fill("120");
  await page.locator("#depreciation:visible").fill("80");
  await page.locator("#change_in_nwc:visible").fill("25");
  await page.locator("#buybacks:visible").fill("15");
  await page.locator("#new_debt_issued:visible").fill("40");
  await page.getByLabel("Valuation date", {exact: true}).fill("2026-11-12");
  await page.getByLabel("Reason for this version").fill("Mock Data updated cash-flow assumptions");
  await page.getByRole("button", { name: "Preview changes" }).click();
  await page.getByRole("button", { name: "Save this reviewed version" }).click();
  await expect(page.getByRole("main").getByText("Reviewed version saved. Previous versions are unchanged.")).toBeVisible();

  const detailUrl = new URL(page.url());
  const modelId = Number(detailUrl.pathname.split("/").at(-1));
  const currentVersions = await backendData<Array<{id: number}>>(page, `/valuation-models/${modelId}/assumptions`);
  const archiveResponse = await backendData<Record<string, unknown>>(page, `/valuation-models/${modelId}/assumptions/${currentVersions[0].id}/export`);
  const downloaded = page.waitForEvent("download");
  await page.getByRole("button", {name: `Export exact saved version #${currentVersions[0].id}`, exact: true}).click();
  const download = await downloaded;
  const file = await download.path();
  const {readFile} = await import("node:fs/promises");
  expect(JSON.parse(await readFile(file!, "utf8"))).toEqual(archiveResponse);
  const assumptionSets = await backendData<Array<{ capex: number; depreciation: number; buybacks: number }>>(
    page,
    `/valuation-models/${modelId}/assumptions`,
  );
  expect(assumptionSets[0].capex).toBe(120);
  expect(assumptionSets[0].depreciation).toBe(80);
  expect(assumptionSets[0].buybacks).toBe(15);

  await page.getByRole("navigation", { name: "Valuation model sections" })
    .getByRole("button", { name: "Sensitivity Tables", exact: true }).click();
  await expect(page.locator(".sensitivity-card:visible")).toHaveCount(6);
  await expect(page.locator(".sensitivity-card:visible").first().getByText(/Canonical FCFF sensitivity v2/)).toBeVisible();
  await expect(page.getByRole("main").getByText(/Colors compare calculated values with the saved assumed market price/)).toBeVisible();
  const saved = await backendData<Array<{
    id: number; outputs: { intrinsic_value_per_share: number };
    sensitivity_tables: Array<{ x_axis_json: { values: number[] }; y_axis_json: { values: number[] }; values_json: Record<string, Record<string, number | null>> }>;
  }>>(page, `/valuation-models/${modelId}/assumptions`);
  for (const table of saved[0].sensitivity_tables) {
    const x = Number(table.x_axis_json.values[2].toFixed(4));
    const y = Number(table.y_axis_json.values[2].toFixed(4));
    const row = Object.entries(table.values_json).find(([key]) => Number(key) === y)![1];
    const center = Object.entries(row).find(([key]) => Number(key) === x)![1];
    expect(center).toBeCloseTo(saved[0].outputs.intrinsic_value_per_share, 8);
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator(".sensitivity-card:visible")).toHaveCount(6);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1)).toBe(true);
  const matrix = page.getByRole("region", { name: /sensitivity table$/ }).first();
  await matrix.focus();
  await expect(matrix).toBeFocused();
  await matrix.press("ArrowRight");
  await expect.poll(() => matrix.evaluate(element => element.scrollLeft)).toBeGreaterThan(0);
  await page.screenshot({ path: test.info().outputPath("sensitivity-mobile.png"), fullPage: true });
  await page.setViewportSize({ width: 1440, height: 1000 });

  await page.getByRole("navigation", { name: "Valuation model sections" })
    .getByRole("button", { name: "Real Options", exact: true }).click();
  await expect(page.getByRole("main").getByText(/^Experimental supplemental analysis/)).toBeVisible();
  await expect(page.getByRole("button", { name: "Calculate Real Option Value", exact: true })).toBeDisabled();

  await page.goto(`/companies/${company.id}/valuation`);
  await expect(page.getByRole("columnheader", { name: "Model readiness" })).toBeVisible();
  const savedModelRow = page.getByRole("row").filter({
    has: page.getByRole("link", { name: `E2E Updated DCF ${unique}`, exact: true }),
  });
  await expect(savedModelRow.getByText("Calculated", { exact: true })).toBeVisible();

  const models = await backendData<Array<{ name: string }>>(
    page,
    `/companies/${company.id}/valuation-models`,
  );
  expect(models.some((model) => model.name === `E2E Updated DCF ${unique}`)).toBeTruthy();
});

test("bind a dated original and recover a first-model receipt after a lost response", async ({page}) => {
  await signIn(page);
  const companies = await backendData<{id:number; ticker:string}[]>(page, "/companies");
  const company = companies.find(item => item.ticker === "E2EFIRST")!;
  const draft = await backendData<{id:number; source_metadata_json:{review_fields:string[]}}>(page,
    `/companies/${company.id}/valuation-drafts`, {method:"POST", data:{}});
  const path = `/valuation-drafts/${draft.id}`;
  const values = Object.fromEntries(Object.entries(ASSUMPTIONS).map(([field,value])=>[field,Number(value)]));
  const inputs = {...values, starting_revenue:null, cash_flow_currency:"USD", discount_rate_currency:"USD",
    projection_years_count:10, revenue_growth_years_json:Object.fromEntries(Array.from({length:10},(_,i)=>[i+1,0])),
    starting_invested_capital:50000000, current_operating_margin:0.2, target_operating_margin:0.2,
    tax_rate:0.25, wacc_start:0.1, wacc_terminal:0.1, terminal_growth_rate:0, terminal_roic:0.1,
    cash:5000000, debt:20000000, diluted_shares:10000000, cross_holdings:0, operating_leases:0};
  await backendData(page, path, {method:"PATCH",data:{assumptions_patch:inputs,reviewed_fields:draft.source_metadata_json.review_fields}});
  await page.goto(`/companies/${company.id}/valuation/draft?draft=${draft.id}`);
  const review = page.getByRole("region", {name:"First valuation preview"});
  await review.getByLabel("Research date").fill("2026-11-12");
  await review.getByText("Choose dated financial evidence").click();
  await review.getByRole("button", {name:"Inspect dated sources"}).click();
  await review.getByRole("combobox", {name:/Revenue/i}).selectOption({index:1});
  await review.getByRole("button", {name:"Apply source selection"}).click();
  await expect(review.getByRole("link", {name:/Inspect original revision/})).toBeVisible();
  await page.reload();
  await expect(review.getByLabel("Research date")).toHaveValue("2026-11-12");
  await review.getByLabel("Reason for this first version").fill("Mock Data dated revenue reviewed against the original filing");
  await review.getByRole("button", {name:"Preview first valuation"}).click();
  const confirm = review.getByRole("button", {name:"Confirm and Create Model"});
  await expect(confirm).toBeEnabled();
  const attempts:string[] = [];
  await page.route(`**/api/backend${path}/confirm`, async route=>{
    attempts.push(route.request().postData()!);
    if (attempts.length === 1) {
      const saved = await route.fetch();
      expect(saved.status()).toBe(201);
      await route.abort("failed");
    } else { await route.continue(); }
  });
  await confirm.click();
  await expect(confirm).toBeEnabled();
  await confirm.click();
  await expect(page).toHaveURL(new RegExp(`/companies/${company.id}/valuation/\\d+$`));
  expect(attempts).toHaveLength(2);
  expect(attempts[1]).toBe(attempts[0]);
});
