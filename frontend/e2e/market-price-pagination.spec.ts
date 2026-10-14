import { expect, test } from "@playwright/test";
import { backendData, createCompany, signIn } from "./helpers";

test("populated price history stays bounded and every filtered page remains reachable", async ({page}) => {
  await signIn(page);
  const ticker = `MOCKP${Date.now().toString().slice(-6)}`;
  const company = await createCompany(page, {ticker, local_symbol:ticker, name:"Mock Data paginated price history"});
  // Deliberately synthetic history in the disposable browser database only.
  const rows = Array.from({length:103}, (_, index) =>
    `${company.id},${ticker},${100 + index},USD,${new Date(Date.UTC(2026, 8, 30 - index)).toISOString().slice(0, 10)}`);
  const imported = await page.request.post("/api/backend/import/market-prices", {
    headers:{origin:new URL(page.url()).origin}, multipart:{file:{name:"Mock Data paginated prices.csv",
      mimeType:"text/csv", buffer:Buffer.from("company_id,ticker,price,currency,as_of_date\n" + rows.join("\n") + "\n")}},
  });
  expect(imported.ok()).toBe(true);
  expect((await imported.json()).data.imported_count).toBe(103);
  const saved = await backendData<Array<{id:number}>>(page, `/market-prices?ticker=${ticker}`);
  expect(saved).toHaveLength(103);
  await page.goto("/market-prices");
  await page.getByLabel("Filter by ticker", {exact:true}).fill(ticker.toLowerCase());
  await page.getByRole("button", {name:"Filter prices", exact:true}).click();
  const forms = page.getByRole("main").locator('form[aria-label="Update market price"]');
  const ids = () => forms.locator('input[name="id"]').evaluateAll(inputs => inputs.map(input => Number((input as HTMLInputElement).value)));
  await expect(forms).toHaveCount(50);
  expect(await ids()).toEqual(saved.slice(0, 50).map(row => row.id));
  await expect(page.getByRole("link", {name:"Previous page", exact:true})).toHaveCount(0);
  await page.getByRole("link", {name:"Next page", exact:true}).click();
  await expect(page.getByRole("main").getByText("Page 2: 50 prices shown", {exact:true})).toBeVisible();
  expect(await ids()).toEqual(saved.slice(50, 100).map(row => row.id));
  expect(new URL(page.url()).searchParams.get("ticker")).toBe(ticker);
  await page.getByRole("link", {name:"Next page", exact:true}).click();
  await expect(forms).toHaveCount(3);
  expect(await ids()).toEqual(saved.slice(100).map(row => row.id));
  await expect(page.getByRole("link", {name:"Next page", exact:true})).toHaveCount(0);
  await page.getByRole("link", {name:"Previous page", exact:true}).click();
  await expect(page.getByRole("main").getByText("Page 2: 50 prices shown", {exact:true})).toBeVisible();
  await page.getByRole("link", {name:"Previous page", exact:true}).click();
  await expect(page.getByRole("main").getByText("Page 1: 50 prices shown", {exact:true})).toBeVisible();
  await page.setViewportSize({width:390, height:844});
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  await page.screenshot({path:test.info().outputPath("market-prices-paginated-mobile.png"), fullPage:true});
  expect(await backendData(page, `/market-prices?ticker=${ticker}`)).toEqual(saved);
  await page.getByLabel("Filter by ticker", {exact:true}).fill("MOCK-NO-MATCH");
  await page.getByRole("button", {name:"Filter prices", exact:true}).click();
  await expect(page.getByRole("main").getByText("No prices match this ticker.", {exact:true})).toBeVisible();
  await expect(page.getByText("No prices match this ticker.", {exact:true}).filter({visible:true})).toHaveCount(1);
  await expect(forms).toHaveCount(0);
});
