import { createHash } from "node:crypto";
import { expect, test, type Page } from "@playwright/test";
import { backendData, createCompany, signIn } from "./helpers";

const headers = "record_type,ticker,price,currency,base_currency,quote_currency,rate,as_of_date,provider_name,provider_symbol,source_url,source_timestamp,price_type\n";
const fixtureFile = (content: string) => ({ name: "Mock Data evidence.csv", mimeType: "text/csv", buffer: Buffer.from(content) });

async function fixture(page: Page, suffix: string, includeHolding = true) {
  const ticker = `P${suffix}${Date.now().toString().slice(-6)}`;
  const company = await createCompany(page, {ticker, local_symbol:ticker, name:`Mock Data import ${suffix}`});
  const portfolio = await backendData<{id:number}>(page, "/portfolios", {method:"POST", data:{name:`Mock Data import ${ticker}`, base_currency:"USD"}});
  if (includeHolding) await backendData(page, "/portfolio-holdings", {method:"POST", data:{portfolio_id:portfolio.id,
    company_id:company.id, ticker, quantity:2, average_cost:100, currency:"USD", as_of_date:"2026-05-01"}});
  return {company, portfolio, ticker};
}

test("portfolio evidence previews do not write; apply checks hashes, duplicates and conflicts", async ({page}) => {
  await signIn(page);
  const {company, portfolio, ticker} = await fixture(page, "I");
  // All values belong only to the disposable Mock Data database. No provider is called.
  const content = headers + `market_price,${ticker},100,USD,,,,2026-05-02,Example Exchange,${ticker},https://example.com/history,2026-05-02T21:00:00Z,close\n`;
  await page.setViewportSize({width:390, height:844});
  await page.goto(`/portfolio/${portfolio.id}?tab=setup`);
  await page.getByRole("main").getByText("Import evidence bundle", {exact:true}).click();
  const panel = page.getByRole("heading", {name:"Source-labeled price and FX evidence"}).locator("../..");
  await expect(panel.getByText(/No evidence file selected/)).toBeVisible();
  const download = await page.request.get(`/api/backend/portfolios/${portfolio.id}/evidence-bundle/template`);
  expect(download.status()).toBe(200);
  expect(await download.text()).toContain(headers.trim());
  await panel.getByLabel("Evidence CSV").setInputFiles(fixtureFile(content));
  await panel.getByRole("button", {name:"Preview evidence", exact:true}).click();
  await expect(panel.getByText("Ready to apply", {exact:true})).toBeVisible();
  await expect(panel.getByText(new RegExp(createHash("sha256").update(content).digest("hex")))).toBeVisible();
  const prices = () => backendData<Array<{company_id:number; price:number}>>(page, `/market-prices?company_id=${company.id}`);
  expect((await prices()).filter(row => row.company_id === company.id)).toHaveLength(0);
  const mismatch = await page.request.post(`/api/backend/portfolios/${portfolio.id}/evidence-bundle/apply`, {
    headers:{origin:new URL(page.url()).origin}, multipart:{file:fixtureFile(content), expected_sha256:"0".repeat(64)},
  });
  expect(mismatch.status()).toBe(409);
  expect((await prices()).filter(row => row.company_id === company.id)).toHaveLength(0);
  await panel.getByRole("button", {name:"Apply 1 fact(s)", exact:true}).click();
  await expect(panel.getByText("Import completed.", {exact:true})).toBeVisible();
  expect((await prices()).filter(row => row.company_id === company.id)).toHaveLength(1);
  await panel.getByLabel("Evidence CSV").setInputFiles(fixtureFile(content));
  await panel.getByRole("button", {name:"Preview evidence", exact:true}).click();
  await expect(panel.getByText("Already imported", {exact:true})).toBeVisible();
  await expect(panel.getByRole("button", {name:"Apply 0 fact(s)", exact:true})).toBeDisabled();
  const retry = await page.request.post(`/api/backend/portfolios/${portfolio.id}/evidence-bundle/apply`, {
    headers:{origin:new URL(page.url()).origin}, multipart:{file:fixtureFile(content), expected_sha256:createHash("sha256").update(content).digest("hex")},
  });
  expect(retry.status()).toBe(200);
  expect((await retry.json()).data).toMatchObject({created_count:0, skipped_duplicate_count:1});
  await panel.getByLabel("Evidence CSV").setInputFiles(fixtureFile(content.replace(",100,USD", ",101,USD")));
  await panel.getByRole("button", {name:"Preview evidence", exact:true}).click();
  await expect(panel.getByText("Blocked", {exact:true})).toBeVisible();
  await expect(panel.getByRole("button", {name:/^Apply \d+ fact/})).toBeDisabled();
  expect((await prices()).filter(row => row.company_id === company.id)[0].price).toBe(100);
  await panel.getByRole("button", {name:"Clear preview", exact:true}).click();
  await expect(panel.getByText(/No evidence file selected/)).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  await page.screenshot({path:test.info().outputPath("evidence-recovery-mobile.png"), fullPage:true});
});

test("late evidence preview cannot follow navigation into another portfolio", async ({page}) => {
  await signIn(page);
  const first = await fixture(page, "L");
  const second = await fixture(page, "N");
  let release!: () => void;
  let entered!: () => void;
  const held = new Promise<void>(resolve => {release=resolve;});
  const started = new Promise<void>(resolve => {entered=resolve;});
  await page.route(`**/portfolios/${first.portfolio.id}/evidence-bundle/preview`, async route => {
    const response = await route.fetch();
    entered();
    await held;
    await route.fulfill({response}).catch(() => {});
  });
  try {
    await page.goto(`/portfolio/${first.portfolio.id}?tab=setup`);
    await page.getByRole("main").getByText("Import evidence bundle", {exact:true}).click();
    // React streams hidden replacement markup outside main during navigation.
    // Operate on the mounted workflow, never a pending server-rendered copy.
    await page.getByRole("main").getByLabel("Evidence CSV").setInputFiles(fixtureFile(headers));
    await page.getByRole("button", {name:"Preview evidence", exact:true}).click();
    await started;
    await expect(page.getByRole("button", {name:"Validating...", exact:true})).toBeVisible();
    await page.goto(`/portfolio/${second.portfolio.id}?tab=setup`);
    release();
    await page.getByRole("main").getByText("Import evidence bundle", {exact:true}).click();
    await expect(page.getByRole("main").getByText(/No evidence file selected/)).toBeVisible();
    await expect(page.getByRole("heading", {name:"Server preview", exact:true})).toHaveCount(0);
    await expect(page.getByRole("button", {name:"Preview evidence", exact:true})).toBeDisabled();
  } finally { release(); }
});

test("correcting recorded activity makes selected historical returns provisional", async ({page}) => {
  await signIn(page);
  // Recording a buy creates its current holding; do not pre-create the same position.
  const {company, portfolio, ticker} = await fixture(page, "C", false);
  for (const [snapshot_date, price] of [["2026-05-02",100],["2026-05-06",110]] as const) {
    await backendData(page, "/market-prices", {method:"POST",data:{company_id:company.id,ticker,price,
      currency:"USD",as_of_date:snapshot_date,provider_name:"Mock Data",price_type:"close"}});
  }
  let purchaseId = 0;
  for (const activity of [
    {company_id:null,ticker:"CASH",transaction_type:"deposit",quantity:200,price:0},
    {company_id:company.id,ticker,transaction_type:"buy",quantity:2,price:100},
  ]) {
    const saved = await backendData<{id:number}>(page, "/portfolio-transactions", {method:"POST",
      data:{...activity,portfolio_id:portfolio.id,fees:0,currency:"USD",transaction_date:"2026-05-01",notes:"Mock Data correction test"}});
    if (activity.transaction_type === "buy") purchaseId = saved.id;
  }
  for (const snapshot_date of ["2026-05-02","2026-05-06"]) {
    const snapshot = await backendData<{calculation_status:string}>(page,
      `/portfolios/${portfolio.id}/snapshots/capture?as_of_date=${snapshot_date}`, {method:"POST"});
    expect(snapshot.calculation_status).toBe("complete");
  }
  const before = await backendData(page, `/portfolio-snapshots?portfolio_id=${portfolio.id}`);
  await page.goto(`/portfolio/${portfolio.id}?tab=performance`);
  await page.getByRole("main").getByLabel("Start Date", {exact:true}).fill("2026-05-02");
  await page.getByRole("main").getByLabel("End Date", {exact:true}).fill("2026-05-06");
  await page.getByRole("button", {name:"Calculate Period", exact:true}).click();
  await expect(page.getByRole("main").getByText("TWR: selected period (complete)", {exact:true})).toBeVisible();
  await page.goto("/portfolio/manage");
  const form = page.getByRole("main").locator(`form:has(input[name="id"][value="${purchaseId}"])`).filter({has:page.getByLabel("Fees", {exact:true})});
  await form.locator("..").getByText("Edit", {exact:true}).click();
  await form.getByLabel("Fees", {exact:true}).fill("1");
  await form.getByRole("button", {name:"Save", exact:true}).click();
  await expect.poll(async () => (await backendData<{fees:number}>(page, `/portfolio-transactions/${purchaseId}`)).fees).toBe(1);
  await page.goto(`/portfolio/${portfolio.id}?tab=performance&start_date=2026-05-02&end_date=2026-05-06`);
  await expect(page.getByRole("main").getByText("TWR: selected period (partial)", {exact:true})).toBeVisible();
  await expect(page.getByRole("main").getByText(/changed activity/).first()).toBeVisible();
  expect(await backendData(page, `/portfolio-snapshots?portfolio_id=${portfolio.id}`)).toEqual(before);
});
