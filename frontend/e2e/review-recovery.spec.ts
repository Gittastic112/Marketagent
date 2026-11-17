import { expect, test } from "@playwright/test";
import { backendData, createCompany, signIn } from "./helpers";

test("sign-in recovers readiness and transport failures without losing entries", async ({ page }) => {
  let checks = 0;
  await page.route("**/api/auth/readiness", route => ++checks === 1 ? route.abort() : route.fulfill({json: {
    configured: true, missing: [], mode: "local_single_user", production_ready: false,
  }}));
  await page.goto("/auth/signin?error=Configuration");
  await page.getByLabel("Username").fill(process.env.LOCAL_AUTH_USERNAME!);
  await page.getByLabel("Password").fill(process.env.LOCAL_AUTH_PASSWORD!);
  await page.getByRole("button", {name: "Check configuration again"}).click();
  await expect(page.getByRole("button", {name: "Sign in", exact: true})).toBeEnabled();
  await page.route("**/api/auth/callback/credentials", route => route.abort());
  await page.getByRole("button", {name: "Sign in", exact: true}).click();
  await expect(page.locator("form").getByRole("alert")).toContainText(/Sign-in/);
  await expect(page.getByLabel("Username")).toHaveValue(process.env.LOCAL_AUTH_USERNAME!);
  await expect(page.getByLabel("Password")).toHaveValue(process.env.LOCAL_AUTH_PASSWORD!);
  await expect(page.getByRole("button", {name: "Sign in", exact: true})).toBeEnabled();
  await page.unroute("**/api/auth/callback/credentials");
  await page.getByRole("button", {name: "Sign in", exact: true}).click();
  await expect(page).toHaveURL("/");
});

test("sign-in keeps an external callback inside the application", async ({ page }) => {
  let external = 0;
  await page.route("https://outside.invalid/**", route => {external += 1; return route.abort();});
  await page.goto("/auth/signin?callbackUrl=" + encodeURIComponent("//outside.invalid/landing"));
  await page.getByLabel("Username").fill(process.env.LOCAL_AUTH_USERNAME!);
  await page.getByLabel("Password").fill(process.env.LOCAL_AUTH_PASSWORD!);
  await page.getByRole("button", {name: "Sign in", exact: true}).click();
  await expect(page).toHaveURL("/");
  expect(external).toBe(0);
});

test("private source approval refreshes its comparison basis and requires a new receipt", async ({ page }) => {
  await signIn(page);
  const companies = await backendData<Array<{id:number; ticker:string}>>(page, "/companies");
  const company = companies.find(row => row.ticker === "BRIEFCMP")!;
  type Comparison = {evidence_hash:string; sources:Array<{id:number; ai_output_id:number; review_status:string}>; reviews:Array<{id:number; field:string; version:number; is_current:boolean}>};
  const url = `/brief-sources/triage?company_id=${company.id}&include_mock=true`;
  const before = await backendData<Comparison>(page, url);
  const source = before.sources[0];
  // A receipt on pending evidence is not an AI approval. Preserve it as history.
  const receipt = await backendData<{id:number; version:number}>(page, "/brief-sources/triage/reviews", {method:"POST",data:{
    company_id:company.id, field:"starting_revenue", include_mock:true, evidence_hash:before.evidence_hash,
    expected_version:before.reviews.find(row => row.field === "starting_revenue")?.version ?? 0,
    disposition:"investigate", notes:"Mock Data pending interpretation requires a separate human review.", evidence_reviewed:true,
  }});
  await page.goto(`/daily-brief/sources/${source.id}`);
  const review = page.getByRole("region", {name:"AI evidence and review"});
  // Revalidate the exact seeded quote so the same production review gate is exercised.
  await review.getByRole("button", {name:"Validate all cited sources"}).click();
  await review.getByLabel("Review notes", {exact:true}).fill("Mock Data: checked the literal period, currency and quote; no financial inputs approved.");
  await expect(review.getByRole("button", {name:"Approve", exact:true})).toBeEnabled();
  await review.getByRole("button", {name:"Approve", exact:true}).click();
  await expect(review).toContainText("Status: approved");
  const after = await backendData<Comparison>(page, url);
  expect(after.evidence_hash).not.toBe(before.evidence_hash);
  expect(after.reviews.find(row => row.id === receipt.id)?.is_current).toBe(false);
  const stale = await page.request.post("/api/backend/brief-sources/triage/reviews", {headers:{origin:new URL(page.url()).origin},data:{
    company_id:company.id, field:"starting_revenue", include_mock:true, evidence_hash:before.evidence_hash,
    expected_version:receipt.version, disposition:"keep_input", notes:"Mock Data stale basis must be rejected.", evidence_reviewed:true,
  }});
  expect(stale.status()).toBe(409);
  const current = await backendData<{id:number; is_current:boolean}>(page,"/brief-sources/triage/reviews",{method:"POST",data:{
    company_id:company.id, field:"starting_revenue", include_mock:true, evidence_hash:after.evidence_hash,
    expected_version:receipt.version, disposition:"keep_input", notes:"Mock Data refreshed evidence reviewed; retain existing inputs.", evidence_reviewed:true,
  }});
  expect(current.is_current).toBe(true);
});

test("thesis evidence navigation, preserving review and company memo download work together", async ({ page }) => {
  await page.setViewportSize({width:1280,height:900});
  await signIn(page);
  const company = await createCompany(page, {ticker:"NINE",local_symbol:"NINE",name:"Mock Data final review company"});
  const note = await backendData<{id:number}>(page,"/thesis-notes",{method:"POST",data:{company_id:company.id,title:"Mock Data preserved thesis",thesis_text:"Original research rationale"}});
  const assumption = await backendData<{id:number}>(page,`/thesis-notes/${note.id}/assumptions`,{method:"POST",data:{thesis_note_id:note.id,description:"Mock Data assumption: recurring profitability requires comparable source periods and separate review of temporary benefits before changing the saved research view."}});
  const event = await backendData<{id:number}>(page,"/events",{method:"POST",data:{company_id:company.id,title:"Mock Data precise event",event_type:"manual",information_speed:"slow"}});
  const impact = await backendData<{id:number}>(page,`/thesis-assumptions/${assumption.id}/impacts`,{method:"POST",data:{event_id:event.id,thesis_assumption_id:assumption.id,impact_classification:"Weakens",rationale:"Retained original counterevidence"}});
  await page.goto(`/companies/${company.id}/thesis?note_id=${note.id}`);
  await page.getByRole("link",{name:"Inspect source event"}).click();
  await expect(page).toHaveURL(`/events/${event.id}/evidence-resolution`);
  await expect(page.getByText("Mock Data precise event",{exact:true}).first()).toBeVisible();
  await page.goto(`/companies/${company.id}/thesis?note_id=${note.id}`);
  const main = page.getByRole("main");
  await main.getByText("Record evidence review",{exact:true}).click();
  const assumptionCells = main.getByRole("region",{name:"Thesis assumptions"}).locator("tbody tr").first().locator("td");
  for (const cell of await assumptionCells.all()) {
    expect(await cell.evaluate(element => element.getBoundingClientRect().width)).toBeGreaterThan(250);
  }
  await page.setViewportSize({width:390,height:844});
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  await page.setViewportSize({width:1280,height:900});
  await main.getByLabel("Review reason").fill("Mock Data complete evidence inspected; retain thesis with counterevidence.");
  await main.getByRole("button",{name:"Reviewed; no thesis change"}).click();
  await expect(main.getByText("reviewed",{exact:true})).toBeVisible();
  await expect(page.getByRole("region", {name:"Thesis assumptions"}).getByText("Retained original counterevidence",{exact:false})).toBeVisible();
  const read = await backendData<{thesis_text:string;changes:unknown[]}>(page,`/thesis-notes/${note.id}`);
  expect(read.thesis_text).toBe("Original research rationale"); expect(read.changes.length).toBe(1);
  const queue = await backendData<{items:Array<{domain:string;record_id:number}>}>(page,"/review-queue");
  expect(queue.items.some(row => row.domain === "thesis" && row.record_id === impact.id)).toBe(false);
  await page.goto(`/companies/${company.id}`);
  const download = page.waitForEvent("download");
  await page.getByRole("link",{name:/Download.*Memo/i}).click();
  const file = await download;
  expect(file.suggestedFilename()).toBe("memo_NINE.md");
  expect(await file.failure()).toBeNull();
});

test("research connection loss offers a read-only result check and never resends", async ({ page }) => {
  test.skip(process.env.E2E_DELAYED_RESEARCH !== "true", "Requires the isolated Mock Data provider fixture");
  await signIn(page);
  const session = await backendData<{id:number}>(page,"/research/sessions",{method:"POST",data:{title:"Mock Data uncertain response"}});
  let posts = 0;
  await page.route(`**/api/backend/research/sessions/${session.id}/messages`, async route => {
    posts += 1;
    await route.fetch(); // The isolated backend commits; only the response is lost.
    await route.abort();
  });
  await page.goto(`/research/sessions/${session.id}`);
  await page.getByRole("checkbox").check();
  await page.getByLabel("Research question").fill("Mock Data uncertainty test question");
  await page.getByRole("button",{name:"Send",exact:true}).click();
  await expect(page.getByRole("button",{name:"Check result",exact:true})).toBeVisible();
  await page.getByRole("button",{name:"Check result",exact:true}).click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText("No request was resent");
  expect(posts).toBe(1);
  const saved = await backendData<{messages:Array<{role:string}>}>(page,`/research/sessions/${session.id}`);
  expect(saved.messages.map(row => row.role)).toEqual(["user","assistant"]);
});

test("narrative claims display their authoring basis and exact private AI provenance", async ({ page }) => {
  test.skip(process.env.E2E_DELAYED_RESEARCH !== "true", "Requires the isolated Mock Data provider fixture");
  await signIn(page);
  const cluster = await backendData<{id:number}>(page,"/narrative-clusters",{method:"POST",data:{name:"Mock Data manual origin"}});
  await backendData(page,"/narrative-claims",{method:"POST",data:{cluster_id:cluster.id,claim_text:"Mock Data manually entered claim"}});
  await backendData(page,"/events",{method:"POST",data:{title:"Mock Data narrative input",description:"Mock Data evidence only",event_type:"manual",information_speed:"slow"}});
  await backendData(page,"/extract?limit=1",{method:"POST",data:{privacy_disclosure_version:"v1"}});
  const claims = await backendData<Array<{id:number;origin:string;ai_output:{id:number;human_review_status:string}|null}>>(page,"/narrative-claims");
  const generated = claims.find(claim => claim.origin === "mock")!;
  expect(generated.ai_output?.human_review_status).toBe("pending");
  await page.goto("/narratives");
  const main = page.getByRole("main");
  const manual = main.locator(`#narrative-${cluster.id}`);
  await expect(manual.getByText("Mock Data manually entered claim",{exact:true})).toBeVisible();
  await expect(manual.getByText("User Assumption",{exact:true})).toBeVisible();
  await expect(main.getByText("Mock Data · Human review: pending",{exact:true}).first()).toBeVisible();
  const generatedRow = main.locator(".brief-item").filter({hasText:"Mock Data: deterministic narrative claim."}).first();
  await generatedRow.getByRole("button",{name:"View Provenance"}).click();
  await expect(generatedRow).toContainText("v1.1.0-narrative-extraction-contract");
  await page.setViewportSize({width:390,height:844});
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  await expect(generatedRow.getByText("Input hash:",{exact:true})).toBeVisible();
});

test("a delayed Mock Data provider completes through the real proxy and is saved once", async ({ page }) => {
  test.skip(process.env.E2E_DELAYED_RESEARCH !== "true", "Requires the isolated delayed-provider app fixture");
  await signIn(page);
  const session = await backendData<{id:number}>(page,"/research/sessions",{method:"POST",data:{title:"Mock Data delayed provider"}});
  await page.goto(`/research/sessions/${session.id}`);
  await page.getByRole("checkbox").check();
  await page.getByLabel("Research question").fill("Mock Data delayed response beyond the ordinary proxy deadline");
  const response = page.waitForResponse(reply => reply.url().endsWith(`/research/sessions/${session.id}/messages`) && reply.request().method() === "POST");
  const started = performance.now();
  await page.getByRole("button",{name:"Send",exact:true}).click();
  expect((await response).status()).toBe(200);
  expect(performance.now() - started).toBeGreaterThan(15_000);
  await expect(page.getByLabel("Research question")).toHaveValue("");
  const saved = await backendData<{messages:Array<{role:string}>;attempts:Array<{execution_status:string}>}>(page,`/research/sessions/${session.id}`);
  expect(saved.messages.map(row => row.role)).toEqual(["user","assistant"]);
  expect(saved.attempts.map(row => row.execution_status)).toEqual(["success"]);
});
