// Uses only fresh disposable Mock Data.
import { expect, test } from "@playwright/test";
import { createHash } from "node:crypto";
import { backendData, createCompany, signIn } from "./helpers";

test("exact event evidence rejects an outdated source, recovers, and reaches saved margin assumptions without changing them", async ({page}) => {
  await signIn(page);
  await page.setViewportSize({width:390, height:844});
  const unique = Date.now().toString().slice(-7);
  const company = await createCompany(page, {ticker:`ER${unique}`, local_symbol:`ER${unique}`, name:"Mock Data evidence resolution"});
  const source = await backendData<{id:number}>(page, "/sources", {method:"POST", data:{
    name:`Mock Data exact-text source ${unique}`, source_type:"filing", active:true,
    base_url:"https://example.invalid/mock-evidence-resolution"}});
  const quote = "Mock Data: Operating margin expanded during the period.";
  const firstText = `Mock Data case ${unique}.\nFirst occurrence: ${quote}\nSecond occurrence: ${quote}`;
  const hash = (text:string) => createHash("sha256").update(text).digest("hex");
  const document = await backendData<{id:number}>(page, "/raw-documents", {method:"POST", data:{
    source_id:source.id, company_id:company.id, document_type:"annual_report",
    title:"Mock Data exact source document", url:"https://example.invalid/mock-evidence-resolution/report",
    published_at:"2026-07-31T12:00:00Z", raw_text:firstText, content_hash:hash(firstText)}});
  const event = await backendData<{id:number}>(page, "/events", {method:"POST", data:{
    company_id:company.id, raw_document_id:document.id, event_type:"filing_update", information_speed:"slow",
    title:"Mock Data margin evidence review", description:quote}});
  const model = await backendData<{id:number}>(page, `/companies/${company.id}/valuation-models`, {method:"POST", data:{
    company_id:company.id, name:"Mock Data margin review model", model_type:"fcff_dcf"}});
  const saved = await backendData<{id:number; updated_at:string; target_operating_margin:number}>(page,
    `/valuation-models/${model.id}/assumptions`, {method:"POST", data:{scenario:"Base",
      story_text:"Mock Data saved assumptions are independent of event evidence", projection_years_count:5,
      starting_revenue:1000, current_operating_margin:0.2, target_operating_margin:0.22, tax_rate:0.25,
      revenue_growth_years_json:{1:0.05,2:0.05,3:0.05,4:0.05,5:0.05}, sales_to_capital_ratio:2.5,
      starting_invested_capital:600, wacc_start:0.1, wacc_terminal:0.09, terminal_growth_rate:0.02,
      terminal_roic:0.12, cash:0, debt:0, diluted_shares:10, net_income:100, book_value_of_equity:500,
      cash_flow_currency:"USD", discount_rate_currency:"USD"}});
  const thesis = await backendData<{id:number}>(page, "/thesis-notes", {method:"POST", data:{
    company_id:company.id, title:"Mock Data margin thesis", thesis_text:"Mock Data: inspect exact source before changing margins", status:"active"}});
  const path = `/events/${event.id}/evidence-resolution`;
  await page.goto(path);
  await page.getByLabel("Exact source phrase", {exact:true}).fill(quote);
  await page.getByRole("button", {name:"Search exact text", exact:true}).click();
  await expect(page.getByRole("heading", {name:"Exact Matches (2)", exact:true})).toBeVisible();
  const secondMatch = page.locator(".brief-item:visible").filter({has:page.getByText("Occurrence 2", {exact:true})});
  await expect(secondMatch).toContainText(quote);
  expect(await backendData<unknown[]>(page, `/events/${event.id}/evidence-references`)).toHaveLength(0);

  // A real source update between search and save must fail on the persisted hash.
  const changedText = `Mock Data revised preamble.\n${firstText}`;
  await backendData(page, `/raw-documents/${document.id}`, {method:"PATCH", data:{
    raw_text:changedText, content_hash:hash(changedText)}});
  await secondMatch.getByRole("button", {name:"Use exact span", exact:true}).click();
  await expect(secondMatch.getByRole("alert")).toContainText("source document changed after the search");
  await expect(page.getByLabel("Exact source phrase", {exact:true})).toHaveValue(quote);
  expect(await backendData<unknown[]>(page, `/events/${event.id}/evidence-references`)).toHaveLength(0);
  await page.screenshot({path:test.info().outputPath("exact-evidence-stale-mobile.png"), fullPage:true});

  await page.getByRole("button", {name:"Search exact text", exact:true}).click();
  await expect(secondMatch.locator('input[name="document_content_hash"]')).toHaveValue(hash(changedText));
  await secondMatch.getByRole("button", {name:"Use exact span", exact:true}).click();
  await expect(page.getByRole("main").getByText("Exact source evidence linked to the event.", {exact:true})).toBeVisible();
  type Reference = {id:number; origin:string; quote:string; start_char:number; end_char:number;
    raw_document_id:number; source_metadata_json:{occurrence_index:number; validated_content_hash:string}};
  const references = await backendData<Reference[]>(page, `/events/${event.id}/evidence-references`);
  expect(references).toHaveLength(1);
  expect(references[0]).toMatchObject({origin:"manual_exact_resolution", raw_document_id:document.id, quote,
    source_metadata_json:{occurrence_index:2, validated_content_hash:hash(changedText)}});
  expect(references[0].start_char).toBe(changedText.lastIndexOf(quote));
  expect(changedText.slice(references[0].start_char,references[0].end_char)).toBe(quote);

  // Repeating the selected span cannot create another reference.
  await page.getByRole("button", {name:"Search exact text", exact:true}).click();
  await expect(secondMatch.getByRole("button", {name:"Use exact span", exact:true})).toBeVisible();
  await secondMatch.getByRole("button", {name:"Use exact span", exact:true}).click();
  await expect(secondMatch.getByRole("alert")).toContainText("already linked to the event");
  expect(await backendData<unknown[]>(page, `/events/${event.id}/evidence-references`)).toHaveLength(1);

  await page.getByRole("navigation", {name:"Next research steps"}).getByRole("link", {name:"Review company thesis", exact:true}).click();
  await expect(page.getByRole("link", {name:"Review or add thesis assumptions", exact:true})).toHaveAttribute("href", `/thesis-notes/${thesis.id}`);
  await page.goto(path);
  await page.getByRole("navigation", {name:"Next research steps"}).getByRole("link", {name:"Inspect saved valuations", exact:true}).click();
  await page.getByRole("link", {name:"Mock Data margin review model", exact:true}).click();
  await page.getByRole("navigation", {name:"Valuation model sections"}).getByRole("combobox", {name:/^Section/}).selectOption("margins");
  await expect(page.getByLabel("Target Operating Margin", {exact:true})).toHaveValue("0.22");
  await page.screenshot({path:test.info().outputPath("event-to-saved-margin-mobile.png"), fullPage:true});
  const after = await backendData<Array<{id:number;updated_at:string;target_operating_margin:number}>>(page, `/valuation-models/${model.id}/assumptions`);
  expect(after).toHaveLength(1);
  expect(after[0]).toMatchObject({id:saved.id, updated_at:saved.updated_at, target_operating_margin:0.22});
  expect(await page.evaluate(() => window.document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
});
