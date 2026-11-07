import {expect, test} from "@playwright/test";
import {signIn} from "./helpers";

test("macro history form expands accessibly and missing segment values stay visible", async ({page}) => {
  await signIn(page);
  await page.setViewportSize({width:390, height:844});
  await page.goto("/macro?tab=top-down");
  await page.getByRole("spinbutton", {name:"Number of periods",exact:true}).fill("9");
  await page.getByRole("button", {name:"Update period count", exact:true}).click();
  await expect(page.getByRole("textbox", {name:"Period 9 label",exact:true})).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  await page.goto("/macro?tab=bottom-up&run=bottom-up&segment_1_name=Mock+Data&segment_1_sic=1234&segment_1_value=");
  await expect(page.getByRole("heading", {name:"Enter a finite number for segment 1 value. Use 0 only when zero is intended.",exact:true})).toBeVisible();
  await expect(page.getByRole("textbox", {name:"Segment 1 name",exact:true})).toHaveValue("Mock Data");
  await page.screenshot({path:test.info().outputPath("macro-validation-mobile.png"),fullPage:true});
});

test("Mock Data regression displays unavailable constant factors without inventing zero exposure", async ({page}) => {
  await signIn(page);
  const query = new URLSearchParams({tab:"top-down",run:"top-down",frequency:"annual",period_count:"3"});
  [[2021,50,80,0],[2022,49.5,78,.01],[2023,48.51,74.08,.02]].forEach(([year,income,value,rate],index) => {
    const p = String(index + 1);
    for (const [field,n] of Object.entries({period:year, operating_income:income,market_cap:value,total_debt:20,
      rate_change:rate,gdp_growth:0,inflation_change:0,currency_change:0})) query.set(field + "_" + p,String(n));
  });
  await page.goto("/macro?" + query);
  await page.locator(".brief-list:visible").filter({has:page.locator('[aria-label="Top-down sensitivity results"]')})
    .getByText("Method and data notes", {exact:true}).click();
  await expect(page.locator("li:visible").filter({hasText:/no observed variation/}).first()).toBeVisible();
  await expect(page.getByRole("cell",{name:"Not available",exact:true}).first()).toBeVisible();
  await expect(page.getByRole("cell",{name:"2",exact:true}).first()).toBeVisible();
  await page.screenshot({path:test.info().outputPath("macro-explicit-history.png"),fullPage:true});
});
