// Recorded public evidence; no external network or AI in this test.
// Official source independently verified on 2026-10-13:
// https://www.apple.com/newsroom/2025/10/apple-reports-fourth-quarter-results/
// Only the 16-word revenue sentence below is quoted. Original release: 2025-10-30;
// reporting quarter ended 2025-09-27. This is dated public evidence, not today's news.
// Dashboard entry is a deterministic live summary, not a newly persisted Daily Brief.
// Combine with the due-scheduler PostgreSQL proof; don't claim real portfolio acceptance.
import { expect, test } from "@playwright/test";
import { createHash } from "node:crypto";
import { backendData, createCompany, signIn } from "./helpers";

test("recorded official evidence remains dated and linked through a morning review with separate Mock Data assumptions", async ({page}) => {
  await signIn(page);
  const companies = await backendData<Array<{id:number;ticker:string;primary_exchange:string;currency:string;name:string}>>(page,"/companies");
  let company = companies.find(row => row.ticker === "AAPL" && row.primary_exchange === "NASDAQ" && row.currency === "USD");
  if (!company) company = {...await createCompany(page,{ticker:"AAPL",local_symbol:"AAPL",name:"Apple Inc.",primary_exchange:"NASDAQ",currency:"USD"}),primary_exchange:"NASDAQ",currency:"USD"};
  const sourceUrl = "https://www.apple.com/newsroom/2025/10/apple-reports-fourth-quarter-results/";
  const quote = "The Company posted quarterly revenue of $102.5 billion, up 8 percent year over year.";
  const sourceDate = "2025-10-30";
  const hash = createHash("sha256").update(quote).digest("hex");
  const source = await backendData<{id:number}>(page,"/sources",{method:"POST",data:{
    name:"Recorded public evidence: Apple Newsroom",source_type:"filing",base_url:sourceUrl,active:true}});
  const document = await backendData<{id:number}>(page,"/raw-documents",{method:"POST",data:{
    source_id:source.id,company_id:company.id,document_type:"earnings_release",
    title:"Recorded public evidence: Apple FY2025 Q4 release, October 30 2025",url:sourceUrl,
    // The source gives a date, not a publication clock time. Midnight is date normalization only.
    published_at:`${sourceDate}T00:00:00Z`,raw_text:quote,content_hash:hash,
    raw_payload_json:{provenance_kind:"recorded_public_evidence",original_publication_date:sourceDate,
      publication_precision:"date_only",fiscal_period_end:"2025-09-27",source_verified_on:"2026-10-13",
      limitation:"A short recorded issuer statement. No independent financial review or current-news claim."}}});
  const event = await backendData<{id:number}>(page,"/events",{method:"POST",data:{
    company_id:company.id,raw_document_id:document.id,event_type:"earnings_release",information_speed:"slow",
    title:"Recorded public evidence: Apple FY2025 Q4 revenue",description:quote,event_time:`${sourceDate}T00:00:00Z`,
    priority_score:100}}); // Priority is a test navigation assumption, not an economic materiality rating.
  const portfolio = await backendData<{id:number}>(page,"/portfolios",{method:"POST",data:{
    name:"Mock Data public-source review portfolio",base_currency:"USD"}});
  await backendData(page,"/portfolio-holdings",{method:"POST",data:{portfolio_id:portfolio.id,
    company_id:company.id,ticker:"AAPL",quantity:1,average_cost:1,currency:"USD",as_of_date:"2025-10-30"}});
  const thesis = await backendData<{id:number}>(page,"/thesis-notes",{method:"POST",data:{
    company_id:company.id,title:"Mock Data review hypothesis for the recorded Apple release",
    thesis_text:"Mock Data: inspect the source period and company statements before changing any forward revenue assumption.",status:"active"}});
  const model = await backendData<{id:number}>(page,`/companies/${company.id}/valuation-models`,{method:"POST",data:{
    company_id:company.id,name:"Mock Data public-source review assumptions",model_type:"fcff_dcf"}});
  const basis = await backendData<{id:number;updated_at:string}>(page,`/valuation-models/${model.id}/assumptions`,{method:"POST",data:{
    scenario:"Base",story_text:"Mock Data assumptions, not approved Apple financials",projection_years_count:5,
    starting_revenue:1000,current_operating_margin:0.2,target_operating_margin:0.22,tax_rate:0.25,
    revenue_growth_years_json:{1:0.05,2:0.05,3:0.05,4:0.05,5:0.05},sales_to_capital_ratio:2.5,
    starting_invested_capital:600,wacc_start:0.1,wacc_terminal:0.09,terminal_growth_rate:0.02,terminal_roic:0.12,
    cash:0,debt:0,diluted_shares:10,net_income:100,book_value_of_equity:500,cash_flow_currency:"USD",discount_rate_currency:"USD"}});
  const noAiRequests:string[]=[];
  page.on("request",request=>{if(request.method()==="POST" && /\/ai\/|\/ai-summary|\/analyze|\/daily-brief(?:\?|$)/.test(new URL(request.url()).pathname)) noAiRequests.push(request.url());});
  await page.setViewportSize({width:390,height:844});
  await page.goto("/");
  const briefPanel = page.locator("section.panel").filter({has:page.getByRole("heading",{name:"Daily Intelligence Brief",exact:true})});
  await briefPanel.getByRole("link",{name:/Recorded public evidence: Apple FY2025 Q4 revenue/}).click();
  const eventPath = `/events/${event.id}/evidence-resolution`;
  await expect(page).toHaveURL(eventPath);
  await expect(page.getByText(quote,{exact:true})).toBeVisible();
  const stored = await backendData<{url:string;published_at:string;content_hash:string;raw_text:string;raw_payload_json:Record<string,unknown>}>(page,`/raw-documents/${document.id}`);
  expect(stored.url).toBe(sourceUrl);
  expect(stored.published_at.slice(0,10)).toBe(sourceDate);
  expect(stored.content_hash).toBe(hash);
  expect(stored.raw_text).toBe(quote);
  expect(stored.raw_payload_json.publication_precision).toBe("date_only");
  const dashboard = await backendData<{daily_brief:{high_materiality_events:Array<{event_id:number;status:string}>}}>(page,"/dashboard/overview");
  expect(dashboard.daily_brief.high_materiality_events.find(row=>row.event_id===event.id)?.status).toBe("Stale");
  await page.getByLabel("Exact source phrase",{exact:true}).fill(quote);
  await page.getByRole("button",{name:"Search exact text",exact:true}).click();
  await expect(page.getByRole("heading",{name:"Exact Matches (1)",exact:true})).toBeVisible();
  await page.getByRole("button",{name:"Use exact span",exact:true}).click();
  await expect(page.getByText("Exact source evidence linked to the event.",{exact:true})).toBeVisible();
  const references = await backendData<Array<{quote:string;source_metadata_json:{validated_content_hash:string}}>>(page,`/events/${event.id}/evidence-references`);
  expect(references).toHaveLength(1);
  expect(references[0].source_metadata_json.validated_content_hash).toBe(hash);
  await page.screenshot({path:test.info().outputPath("recorded-public-evidence-mobile.png"),fullPage:true});

  const steps=page.getByRole("navigation",{name:"Next research steps"});
  await steps.getByRole("link",{name:"Review company thesis",exact:true}).click();
  await page.getByRole("link",{name:"Review or add thesis assumptions",exact:true}).click();
  // If a preexisting AAPL active thesis wins the default link, select the exact new test note explicitly.
  // Root may prefer a separate disposable identity if AAPL already has an active note.
  await expect(page).toHaveURL(`/thesis-notes/${thesis.id}`);
  const assumption="Mock Data next review: compare the dated revenue statement with reviewed financials before updating a forecast.";
  await page.getByLabel("Description",{exact:true}).fill(assumption);
  await page.getByRole("button",{name:"Add Assumption",exact:true}).click();
  await expect(page.getByRole("cell",{name:assumption,exact:true})).toBeVisible();
  await page.goto(eventPath);
  await steps.getByRole("link",{name:"Inspect saved valuations",exact:true}).click();
  await page.getByRole("link",{name:"Mock Data public-source review assumptions",exact:true}).click();
  await page.getByRole("navigation",{name:"Valuation model sections"}).getByRole("combobox",{name:/^Section/}).selectOption("revenue");
  await expect(page.getByLabel("Year-by-Year Revenue Growth (JSON)",{exact:true})).toHaveValue(/"1"\s*:\s*0\.05/);
  const unchanged = await backendData<Array<{id:number;updated_at:string}>>(page,`/valuation-models/${model.id}/assumptions`);
  expect(unchanged).toHaveLength(1);
  expect(unchanged[0]).toMatchObject({id:basis.id,updated_at:basis.updated_at});
  await page.goto(eventPath);
  await steps.getByRole("link",{name:"Record next review action",exact:true}).click();
  const rationale="Mock Data review action: verify the FY2025 Q4 period against reviewed statements; recorded public evidence does not authorize a forecast change.";
  await page.getByLabel("Decision",{exact:true}).selectOption("Pass");
  await page.getByLabel("Rationale",{exact:true}).fill(rationale);
  await page.getByRole("button",{name:"Record Decision",exact:true}).click();
  await expect(page.getByText(rationale,{exact:true})).toBeVisible();
  expect(noAiRequests).toEqual([]);
  expect(await page.evaluate(()=>window.document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
  await page.screenshot({path:test.info().outputPath("recorded-public-next-review-mobile.png"),fullPage:true});
});
