import { expect, test } from "@playwright/test";
import { backendData, createCompany, signIn } from "./helpers";
import { verifyRoutes } from "./route-checks";

for (const width of [1440, 390]) {
  test(`company price and recorded financial units remain truthful at ${width}px`, async ({ page }, testInfo) => {
    await signIn(page);
    const companies = await backendData<Array<{id:number; ticker:string}>>(page, "/companies");
    const company = companies.find(row => row.ticker === "E2EINR")!;
    expect(company).toBeTruthy();
    await page.setViewportSize({width, height:900});
    await page.goto(`/companies/${company.id}`);
    const main = page.getByRole("main");
    await expect(main.getByText("Recorded alerts", {exact:true})).toBeVisible();
    await expect(main.getByText("Risk Status", {exact:true})).toHaveCount(0);
    await expect(main.getByText("INR 1,250", {exact:true})).toBeVisible();
    await main.getByText("Quote source and timing", {exact:true}).click();
    await expect(main.getByText(/Source: Mock Data provider/)).toBeVisible();
    await expect(main.getByText(/Source timestamp: 2026-09-30/)).toBeVisible();
    await expect(main.getByText(/Delay unknown/)).toBeVisible();
    const financial = main.getByRole("heading", {name:"Financial Trends", exact:true}).locator("../..");
    await expect(financial.getByText("INR million", {exact:true})).toHaveCount(2);
    await expect(financial.getByText("Unit unknown", {exact:true})).toBeVisible();
    await expect(financial.getByText(/Report date: 2026-05-31/)).toBeVisible();
    await expect(financial.getByText(/Recorded metrics may be unreviewed/)).toBeVisible();
    expect(await financial.innerText()).not.toContain("$");
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    await page.screenshot({path:testInfo.outputPath(`company-inr-${width}.png`), fullPage:true});
    await financial.getByRole("link", {name:"Review financial sources and normalized coverage"}).click();
    await expect(page).toHaveURL(`/companies/${company.id}/fundamentals`);
    await expect(main.getByRole("heading", {name:"Normalization Coverage", exact:true})).toBeVisible();
    await expect(main.getByLabel("Upload Screener.in Export (.xlsx)", {exact:true})).toBeVisible();
    await verifyRoutes(page, testInfo, [["india-fundamentals", `/companies/${company.id}/fundamentals`]],
      {width, height:900}, "Isolated Mock Data India financial coverage");
  });
}

test("company with no stored quote or financials explains the missing coverage", async ({ page }) => {
  await signIn(page);
  const ticker = `G${Date.now().toString().slice(-8)}`;
  const company = await createCompany(page, { ticker, local_symbol:ticker, name:"Mock Data coverage gap",
    market:"IN", primary_exchange:"NSE", currency:"INR", country:"India" });
  await page.goto(`/companies/${company.id}`);
  await expect(page.getByRole("main").getByText("No stored quote for this company.", {exact:true})).toBeVisible();
  await expect(page.getByRole("link", {name:"Check price provider health"})).toBeVisible();
  await expect(page.getByRole("main").getByText("No recorded financial periods.", {exact:true})).toBeVisible();

  const portfolio = await backendData<{id:number}>(page, "/portfolios", {method:"POST",data:{
    name:`Mock Data coverage ${ticker}`,base_currency:"USD"}});
  await backendData(page, "/portfolio-holdings", {method:"POST",data:{portfolio_id:portfolio.id,
    company_id:company.id,ticker,quantity:1,average_cost:100,currency:"INR",as_of_date:"2026-05-01"}});
  await page.goto(`/portfolio/${portfolio.id}`);
  const main = page.getByRole("main");
  await expect(main.getByText("No price", {exact:true})).toBeVisible();
  await expect(main.getByText(/Missing FX: INR\/USD/)).toBeVisible();
  await expect(main.getByRole("region", {name:"Portfolio summary"}).getByText("Not available", {exact:true})).not.toHaveCount(0);
  await backendData(page, "/market-prices", {method:"POST",data:{company_id:company.id,ticker,price:1250,
    currency:"INR",as_of_date:"2026-05-02",provider_name:"Mock Data",price_type:"close"}});
  await page.reload();
  await expect(main.getByText("Stale", {exact:true})).toBeVisible();
  await expect(main.getByText(/Missing FX: INR\/USD/)).toBeVisible();
  await expect(main.getByText(/2026-05-02/)).toBeVisible();
});

test("unsupported automatic market modules expose their input boundary", async ({ page }) => {
  await signIn(page);
  await page.goto("/portfolio/regime");
  const main = page.getByRole("main");
  await expect(main.getByText(/Automatic options, liquidity, volume and breadth feeds are not available yet/)).toBeVisible();
  await expect(main.getByRole("heading", {name:"Market context score", exact:true})).toBeVisible();
  await expect(main.getByText("No regime inputs are recorded.", {exact:true})).toBeVisible();
  await expect(main.getByText("N/A", {exact:true})).toBeVisible();
  await expect(main.getByRole("heading", {name:"Entry Timing Readiness", exact:true})).toHaveCount(0);
});
