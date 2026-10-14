import { expect, test } from "@playwright/test";
import { backendData, createCompany, signIn } from "./helpers";
import type { BriefSource } from "../lib/api/brief-sources";
import type { BriefTriage, ComparisonReview } from "../lib/api/brief-triage";

test("duplicate intake preserves archived original evidence and explicit restore keeps its review state", async ({page}) => {
  await signIn(page);
  const unique = Date.now().toString().slice(-7);
  const company = await createCompany(page, {ticker: `BR${unique}`, local_symbol: `BR${unique}`, name: "Mock Data source recovery"});
  const original = await backendData<BriefSource>(page, "/brief-sources", {method: "POST", data: {
    company_id: company.id, title: "Mock Data original recovery source",
    text: "Mock Data: This immutable original passage must survive duplicate intake, archive and restore.", as_of_date: "2026-01-02"}});
  const archived = await backendData<BriefSource>(page, `/brief-sources/${original.id}/lifecycle`, {
    method: "POST", data: {archived: true, expected_version: original.lifecycle_version}});
  await page.setViewportSize({width: 390, height: 844});
  await page.goto("/daily-brief");
  const intake = page.getByRole("group", {name: "Add a private research source"});
  await intake.getByLabel(/^Company/).selectOption(String(company.id));
  await intake.getByLabel("Source title", {exact: true}).fill("Mock Data attempted replacement title");
  await intake.getByLabel("Source date, if known", {exact: true}).fill("2026-01-02");
  await intake.getByLabel("Source text", {exact: true}).fill("Mock Data: This immutable original passage must survive duplicate intake, archive and restore.");
  await page.getByRole("button", {name: "Save source privately"}).click();
  await expect(page.getByRole("main").getByText(/already exists in your archive/)).toBeVisible();
  await page.getByRole("link", {name: "Inspect saved source: Mock Data original recovery source"}).click();
  await expect(page.locator(".brief-source-text")).toContainText("immutable original passage");
  await page.getByRole("button", {name: "Restore source", exact: true}).click();
  await expect(page.getByRole("button", {name: "Archive source", exact: true})).toBeVisible();
  const restored = await backendData<BriefSource>(page, `/brief-sources/${original.id}`);
  expect(restored.id).toBe(original.id);
  expect(restored.title).toBe(original.title);
  expect(restored.source_sha256).toBe(original.source_sha256);
  expect(restored.as_of_date).toBe(original.as_of_date);
  expect(restored.lifecycle_version).toBe(archived.lifecycle_version + 1);
  expect(restored.analysis_status).toBe("not_scanned");
  expect(restored.review_status).toBe(original.review_status);
  await page.screenshot({path: test.info().outputPath("duplicate-archive-restore-mobile.png"), fullPage: true});
});

test("unconfigured scan is explicit and late retry failure cannot follow navigation", async ({page}) => {
  await signIn(page);
  const unique = Date.now().toString().slice(-7);
  const company = await createCompany(page, {ticker: `SC${unique}`, local_symbol: `SC${unique}`, name: "Mock Data scan recovery"});
  const source = await backendData<BriefSource>(page, "/brief-sources", {method: "POST", data: {
    company_id: company.id, title: "Mock Data interrupted scan",
    text: "Mock Data: A private source for controlled scan failure and navigation verification only."}});
  await page.goto("/daily-brief");
  const library = page.getByRole("region", {name: "Saved research sources"});
  await library.getByLabel("Filter by company").selectOption(String(company.id));
  await library.getByRole("button", {name: "Search sources", exact: true}).click();
  await expect(library.locator(".brief-source-card")).toHaveCount(1);
  await expect(library.getByRole("button", {name: "Scan with AI", exact: true})).toBeDisabled();
  await page.getByRole("checkbox", {name: /I understand this data will be sent/}).check();
  await library.getByRole("button", {name: "Scan with AI", exact: true}).click();
  await expect(page.getByRole("alert").filter({hasText: /AI is not configured/})).toBeVisible();
  expect((await backendData<BriefSource>(page, `/brief-sources/${source.id}`)).analysis_status).toBe("failed");
  let release!: () => void;
  const held = new Promise<void>(resolve => {release = resolve;});
  let began!: () => void;
  const started = new Promise<void>(resolve => {began = resolve;});
  let attempts = 0;
  await page.route(`**/api/backend/brief-sources/${source.id}/analyze`, async route => {
    attempts++; began(); await held;
    await route.fulfill({status: 504, json: {errors: [{message: "Mock Data delayed timeout"}]}}).catch(() => {});
  });
  try {
    await library.getByRole("button", {name: "Retry scan", exact: true}).click();
    await started;
    await expect(page.getByRole("button", {name: "Save source privately"})).toBeDisabled();
    await expect(library.getByRole("button", {name: "Archive source", exact: true})).toBeDisabled();
    await page.goto("/companies");
    release();
    await expect(page.getByRole("heading", {name: "Companies", exact: true})).toBeVisible();
    await expect(page.getByText("Mock Data delayed timeout", {exact: true})).toHaveCount(0);
    await page.goto("/daily-brief");
    await expect(page.getByRole("button", {name: "Save source privately"})).toBeEnabled();
    await expect(page.getByText("Mock Data delayed timeout", {exact: true})).toHaveCount(0);
    expect(attempts).toBe(1);
  } finally {release();}
});

test("stale comparison save retains the rationale and immutable history survives explicit recovery", async ({page}) => {
  await signIn(page);
  const companies = await backendData<Array<{id: number; ticker: string}>>(page, "/companies");
  const company = companies.find(item => item.ticker === "BRIEFCMP")!;
  const before = await backendData<BriefTriage>(page, `/brief-sources/triage?company_id=${company.id}&include_mock=true`);
  const source = before.sources[0];
  const group = before.groups.find(item => item.field === "starting_revenue")!;
  const oldVersion = before.reviews.find(item => item.field === group.field)?.version ?? 0;
  await page.goto(`/daily-brief/triage?company_id=${company.id}`);
  await page.getByRole("checkbox", {name: "Include clearly labeled Mock Data"}).check();
  const review = page.getByRole("region", {name: `${group.label} analyst review`});
  const rationale = "Mock Data: I need to retain this rationale while resolving changed source evidence.";
  await review.getByLabel(`Rationale for ${group.label}`).fill(rationale);
  await review.getByRole("checkbox", {name: /I reviewed the displayed passages/}).check();
  const archived = await backendData<BriefSource>(page, `/brief-sources/${source.id}/lifecycle`, {
    method: "POST", data: {archived: true, expected_version: source.lifecycle_version}});
  try {
    await review.getByRole("button", {name: "Save analyst review"}).click();
    await expect(review.getByRole("alert")).toContainText("Refresh comparison");
    await expect(review.getByLabel(`Rationale for ${group.label}`)).toHaveValue(rationale);
    const unchanged = await backendData<ComparisonReview[]>(page, `/brief-sources/triage/reviews?company_id=${company.id}&field=${group.field}&include_mock=true`);
    expect(unchanged[0]?.version ?? 0).toBe(oldVersion);
  } finally {
    await backendData(page, `/brief-sources/${source.id}/lifecycle`, {method: "POST", data: {archived: false, expected_version: archived.lifecycle_version}});
  }
  await page.getByRole("button", {name: "Refresh comparison", exact: true}).click();
  await review.getByLabel(`Rationale for ${group.label}`).fill(rationale);
  await review.getByRole("checkbox", {name: /I reviewed the displayed passages/}).check();
  await review.getByRole("button", {name: "Save analyst review"}).click();
  await expect(page.getByRole("main").getByText(/Analyst review recorded/)).toBeVisible();
  await review.getByRole("button", {name: "Show review history"}).click();
  await expect(review.getByRole("link", {name: `Version ${oldVersion + 1} · Investigate further`})).toBeVisible();
  const history = await backendData<ComparisonReview[]>(page, `/brief-sources/triage/reviews?company_id=${company.id}&field=${group.field}&include_mock=true`);
  expect(history[0].notes).toBe(rationale);
  expect(history[0].version).toBe(oldVersion + 1);
  expect(history[0].is_current).toBe(true);
  if (oldVersion) expect(history[1].version).toBe(oldVersion);
});
