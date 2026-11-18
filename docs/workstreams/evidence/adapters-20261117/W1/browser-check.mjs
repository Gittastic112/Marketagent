// Mock Data verification against the real Next components, never a normal backend.
// Requires the temporary fixture-page.tsx mounted at app/w1-ui-check/page.tsx.
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const repository = resolve(import.meta.dirname, "../../../../..");
const require = createRequire(resolve(repository, "frontend/package.json"));
const { chromium, expect } = require("@playwright/test");
const AxeBuilder = require("@axe-core/playwright").default;
const output = resolve(import.meta.dirname, "browser-output");
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/chromium", headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1050 } });
const failures = [];
page.on("pageerror", error => failures.push(error.message));
const meta = { status: "success", last_updated: "2026-11-17T10:00:00Z", source: "Mock Data browser fixture", is_stale: false, is_mock: true, warnings: [], confidence: "none", processing_time_ms: 1 };
const envelope = data => ({ data, meta, errors: [] });
const fixtureCompany = (id, market, exchange) => ({ id, ticker: "ABC", name: `Mock Data ${market} company`, market, primary_exchange: exchange, currency: market === "IN" ? "INR" : "USD", aliases_json: [], active: true });
const companies = [fixtureCompany(7, "US", "NYSE"), fixtureCompany(8, "IN", "NSE")];
const evidence = version => ({ valuation_model_id: 7, assumption_set_id: version, scenario: "Base", assumptions_updated_at: "2026-11-17T10:00:00Z", output_id: version + 8,
  output_calculated_at: "2026-11-17T10:00:00Z", currency: "USD", ai_output_id: version + 100, claim_type: "AI Interpretation", is_current: true, basis_verified: true,
  provider_name: "mock", model_name: "Mock Data", prompt_version: "fixture/v1", input_hash: "a".repeat(64), source_ids: ["valuation:7", `dcf_assumption_set:${version}`],
  generated_at: "2026-11-17T10:00:00Z", review_status: "pending", is_mock: true, confidence_label: "not_evaluated", limitations: "Mock Data fixture; no provider called", interpretation_quality: "not_evaluated" });
let releaseGeneration;
let generationStarted = false;
let releaseEvidence;
let evidenceStarted = false;
let releasePreview;
let previewStarted = false;
let holdPreview = false;
const posts = [];
let savedRun;
const runResult = (id, kind) => ({ run_id: id, kind, status: "complete", manifest: { schema_version: "research-lab/v1", input_sha256: "a".repeat(64), output_sha256: "b".repeat(64), created_at: "2026-11-17T10:00:00Z", adapter: "Mock Data native fixture", adapter_version: "1", dependencies: {}, source_assertion: "user_supplied_unverified", valuation_as_of: "2025-01-22", public_information_cutoff: null, application_observed_cutoff: null, snapshot_created_at: "2026-11-17T10:00:00Z", knowledge_policy: "unverified_research", deterministic_seed: 0 },
  result: kind === "allocation" ? { weights: { A: 0.5, B: 0.5 }, metrics: { annualized_volatility: 0.12, annual_expected_return: null, sharpe_ratio: null }, base_currency: "USD", return_basis: "total_return" }
    : { metrics: { total_return: 0.01, max_drawdown: -0.02 }, equity_curve: [{ date: "2025-01-03", wealth_index: 1.02, return_decimal: 0.02, drawdown: 0 }, { date: "2025-01-06", wealth_index: 1.01, return_decimal: -0.0098039216, drawdown: -0.0098039216 }], final_weights: { A: 0.5, B: 0.5 }, base_currency: "USD", return_basis: "total_return" }, warnings: ["Mock Data transport fixture. No calculation or provider was called."] });

await page.route("**/api/backend/**", async route => {
  const request = route.request();
  const url = new URL(request.url());
  const path = url.pathname.replace("/api/backend", "");
  if (request.method() === "POST") posts.push({ path, body: request.postData() });
  if (path === "/companies") return route.fulfill({ json: envelope(companies) });
  if (path === "/companies/lookup") return route.fulfill({ json: envelope({ ticker: url.searchParams.get("ticker"), name: "Mock Data lookup", market: "IN", primary_exchange: "NSE", currency: "INR", source: "Mock Data provider", warnings: [] }) });
  if (path === "/search/evidence") {
    const query = url.searchParams.get("q");
    if (query === "alpha") { evidenceStarted = true; await new Promise(resolve => { releaseEvidence = resolve; }); }
    return route.fulfill({ json: envelope([{ result_type: "document", record_id: query === "alpha" ? 1 : 2, company_id: 7, title: `Mock Data ${query} evidence`, excerpt: "Fixture excerpt", rank: 1, claim_type: "Fact", scope: "shared", review_status: "not_applicable", is_mock: true, source_name: "Mock Data source", source_timestamp: "2026-11-17T10:00:00Z", href: "/documents/2/sections", locator: null }]) });
  }
  if (path.includes("/ai/memo")) {
    const version = request.method() === "POST" ? request.postDataJSON().assumption_set_id : Number(url.searchParams.get("assumption_set_id"));
    if (request.method() === "POST") { generationStarted = true; await new Promise(resolve => { releaseGeneration = resolve; }); }
    return route.fulfill({ json: envelope({ memo_markdown: `# Mock Data saved version ${version}\n\n| Input | Value |\n| --- | --- |\n| WACC | 9% |\n\n[source_id:valuation:7] [source_id:document:999]\n\n[unsafe](javascript:alert(1))\n\n<script>window.untrustedMemoExecuted=true</script>\n\n![remote](https://example.invalid/tracker.png)`, is_mock: true, evidence: evidence(version) }) });
  }
  if (path.includes("/evidence-bundle/preview")) {
    const portfolioId = Number(path.split("/")[2]);
    if (holdPreview) { previewStarted = true; await new Promise(resolve => { releasePreview = resolve; }); }
    const valid = request.postData()?.includes("valid-evidence.csv");
    const rows = Array.from({ length: 125 }, (_, index) => ({ row_index: index + 2, record_type: index % 2 ? "fx_rate" : "market_price", action: !valid && index % 17 === 0 ? "error" : index % 3 === 0 ? "skip" : "create", message: "Mock Data preview result", errors: !valid && index % 17 === 0 ? [{ row_index: index + 2, field: "source_url", message: "Mock Data missing provenance" }] : [] }));
    return route.fulfill({ json: envelope({ is_preview: true, filename: valid ? "valid-evidence.csv" : "review-evidence.csv", content_sha256: valid ? "c".repeat(64) : "d".repeat(64), byte_size: 128, total_rows: 125, create_count: rows.filter(row => row.action === "create").length, skip_count: rows.filter(row => row.action === "skip").length, error_count: rows.filter(row => row.action === "error").length, market_price_count: 63, fx_rate_count: 62, can_apply: valid, claim_type: "Fact", contains_mock_data: false, scope: { portfolio_id: portfolioId, portfolio_name: "Mock Data transport scope", holding_tickers: ["ABC"], benchmark_ticker: null, allowed_fx_pairs: ["INR/USD"] }, rows }) });
  }
  if (path.includes("/evidence-bundle/apply")) return route.fulfill({ json: envelope({ status: "completed", processing_run_id: 71, content_sha256: "c".repeat(64), created_count: 83, market_prices_created: 42, fx_rates_created: 41, skipped_duplicate_count: 42, contains_mock_data: false, claim_type: "Fact" }) });
  if (path === "/api/research-lab/capabilities") return route.fulfill({ json: envelope({ adapters: [{ id: "native", label: "Mock Data native fixture", available: true, version: "1", reason: null }, { id: "PyPortfolioOpt", label: "Constrained allocation", available: false, version: null, reason: "Mock Data optional dependency missing" }], limits: { max_assets: 40, max_observations: 2600 }, warnings: [] }) });
  if (path === "/api/research-lab/runs") return route.fulfill({ json: envelope(savedRun ? [{ run_id: savedRun.run_id, kind: savedRun.kind, status: "success", created_at: savedRun.manifest.created_at, input_sha256: savedRun.manifest.input_sha256, adapter: "Mock Data" }] : []) });
  if (path.match(/^\/api\/research-lab\/runs\/\d+\/export$/)) return route.fulfill({ contentType: "application/json", headers: { "Content-Disposition": 'attachment; filename="mock-data-run.json"' }, body: JSON.stringify(savedRun) });
  if (path.match(/^\/api\/research-lab\/runs\/\d+$/)) return route.fulfill({ json: envelope(savedRun) });
  if (["/api/research-lab/allocation", "/api/research-lab/simulation"].includes(path)) {
    const kind = path.split("/").at(-1); savedRun = runResult(kind === "allocation" ? 42 : 43, kind);
    return route.fulfill({ json: envelope(savedRun) });
  }
  if (path === "/api/source-adapters") return route.fulfill({ json: envelope([{ adapter: "edgartools", available: true, status: "Mock Data configured fixture", dependency_version: "fixture", warnings: [] }]) });
  if (path.includes("/source-adapters/")) return route.fulfill({ json: envelope({ adapter: "Mock Data source", processing_run_id: 81, raw_document_ids: [9], candidate_ids: [101], fetched_count: 1, created_count: 1, duplicate_count: 0, status: "partial", observed_at: "2026-11-17T10:00:00Z", warnings: ["Mock Data receipt"], details: { coverage: "partial" } }) });
  if (path === "/api/data-adapters/calendars/schedule") return route.fulfill({ json: envelope({ provider: "Mock Data calendar", observed_at: "2026-11-17T10:00:00Z", processing_run_id: 82, source_document_ids: [10], result: { exchange: "XNYS", coverage_start: "2025-01-01", coverage_end: "2025-01-10", timezone: "America/New_York", sessions: [], warnings: ["Mock Data transport fixture"] }, warnings: ["Mock Data fixture"] }) });
  return route.fulfill({ status: 503, json: { data: null, meta: { ...meta, status: "unavailable" }, errors: [{ code: "MOCK_UNAVAILABLE", message: `Mock Data route unavailable: ${path}` }] } });
});

const checks = [];
async function capture(name) {
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true, `${name}: horizontal page overflow`);
  await page.screenshot({ path: resolve(output, `${name}.png`), fullPage: true });
  const axe = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"]).analyze();
  await writeFile(resolve(output, `${name}-axe.json`), JSON.stringify(axe.violations, null, 2));
  assert.deepEqual(axe.violations.map(violation => ({ id: violation.id, targets: violation.nodes.map(node => node.target) })), [], `${name}: accessibility`);
}
try {
  await page.goto("http://127.0.0.1:13117/auth/signin?callbackUrl=/w1-ui-check");
  await page.getByLabel("Username").fill("w1-mock-data");
  await page.getByLabel("Password").fill("mock-data-local-check");
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Mock Data UI verification" })).toBeVisible();
  const memo = page.getByRole("region", { name: "Valuation memo", exact: true });
  await expect(memo.getByRole("heading", { name: "Mock Data saved version 11" })).toBeVisible();
  await expect(memo.getByRole("table")).toHaveCount(1);
  await expect(memo.getByRole("link", { name: "[source_id:valuation:7]", exact: true })).toHaveAttribute("href", "#memo-7-11-111-source-1");
  await expect(memo.getByText(/unresolved citation/)).toBeVisible();
  assert.equal(await page.evaluate(() => "untrustedMemoExecuted" in window), false);
  await expect(memo.locator("img,script,a[href^='javascript:']")).toHaveCount(0);
  await memo.getByRole("checkbox").check();
  await memo.getByRole("button", { name: "Regenerate Memo" }).click();
  await expect.poll(() => generationStarted).toBe(true);
  await page.getByRole("button", { name: "Version 12", exact: true }).click();
  await expect(memo.getByRole("heading", { name: "Mock Data saved version 12" })).toBeVisible();
  releaseGeneration();
  await expect(memo.getByRole("heading", { name: "Mock Data saved version 11" })).toHaveCount(0);
  const memoDownload = page.waitForEvent("download");
  await memo.getByRole("button", { name: "Download memo with evidence" }).click();
  const downloadedMemo = await memoDownload;
  assert.equal(downloadedMemo.suggestedFilename(), "valuation-7-assumptions-12-memo-112.md");
  await downloadedMemo.saveAs(resolve(output, "mock-data-memo.md"));
  assert.ok((await readFile(resolve(output, "mock-data-memo.md"), "utf8")).includes('"assumption_set_id": 12'));
  checks.push("memo Markdown/table/citation safety, late generation isolation and artifact-bound .md download");

  await page.getByLabel("Evidence CSV", { exact: true }).setInputFiles({ name: "review-evidence.csv", mimeType: "text/csv", buffer: Buffer.from("Mock Data preview fixture") });
  await page.getByRole("button", { name: "Preview evidence", exact: true }).click();
  await expect(page.getByRole("region", { name: "Evidence preview rows", exact: true }).getByRole("row")).toHaveCount(51);
  await page.getByLabel("Row status", { exact: true }).selectOption("error");
  await expect(page.getByRole("region", { name: "Evidence preview rows", exact: true }).getByRole("row")).toHaveCount(9);
  await page.getByRole("button", { name: "Next error", exact: true }).click();
  await expect(page.locator("tr.evidence-row-selected")).toContainText("2");
  await page.getByRole("button", { name: "Next error", exact: true }).click();
  await expect(page.locator("tr.evidence-row-selected")).toContainText("19");
  await expect(page.getByRole("button", { name: /Apply \d+ fact/ })).toBeDisabled();
  await page.getByRole("button", { name: "Clear preview", exact: true }).click();
  holdPreview = true;
  await page.getByLabel("Evidence CSV", { exact: true }).setInputFiles({ name: "review-evidence.csv", mimeType: "text/csv", buffer: Buffer.from("Mock Data stale preview") });
  await page.getByRole("button", { name: "Preview evidence", exact: true }).click();
  await expect.poll(() => previewStarted).toBe(true);
  await page.getByRole("button", { name: "Portfolio 8", exact: true }).click();
  holdPreview = false; releasePreview();
  await expect(page.getByRole("heading", { name: "Server preview", exact: true })).toHaveCount(0);
  await page.getByLabel("Evidence CSV", { exact: true }).setInputFiles({ name: "valid-evidence.csv", mimeType: "text/csv", buffer: Buffer.from("Mock Data exact valid file bytes") });
  await page.getByRole("button", { name: "Preview evidence", exact: true }).click();
  await page.getByLabel("Row status", { exact: true }).selectOption("skip");
  await page.getByRole("button", { name: "Apply 83 fact(s)", exact: true }).click();
  await expect(page.getByText("Import completed.", { exact: true })).toBeVisible();
  const apply = posts.find(post => post.path.endsWith("/evidence-bundle/apply"));
  assert.ok(apply.body.includes("c".repeat(64)) && apply.body.includes("Mock Data exact valid file bytes"));
  checks.push("evidence filtering, pagination, source-row navigation, blocked errors, stale-portfolio isolation and exact bytes/hash apply");

  await page.getByRole("button", { name: "Search companies and evidence", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Find research", exact: true });
  await dialog.getByLabel("Search terms", { exact: true }).fill("ABC");
  await expect(dialog.getByRole("link", { name: /Mock Data US company/ })).toBeVisible();
  await expect(dialog.getByRole("link", { name: /Mock Data IN company/ })).toBeVisible();
  await dialog.getByRole("button", { name: "Stored evidence", exact: true }).click();
  await dialog.getByLabel("Search terms", { exact: true }).fill("alpha");
  await expect.poll(() => evidenceStarted).toBe(true);
  await dialog.getByLabel("Search terms", { exact: true }).fill("beta");
  await expect(dialog.getByRole("link", { name: /Mock Data beta evidence/ })).toBeVisible();
  releaseEvidence();
  await expect(dialog.getByRole("link", { name: /Mock Data alpha evidence/ })).toHaveCount(0);
  await dialog.getByLabel("Search terms", { exact: true }).press("ArrowDown");
  await expect(dialog.getByRole("link", { name: /Mock Data beta evidence/ })).toBeFocused();
  await capture("palette-desktop");
  await page.keyboard.press("Escape");
  await expect(page.getByRole("button", { name: "Search companies and evidence", exact: true })).toBeFocused();
  checks.push("palette identity distinction, latest evidence response, arrow navigation, Escape and restored focus");
  await capture("memo-import-desktop");
  await page.setViewportSize({ width: 390, height: 844 });
  await capture("memo-import-mobile");

  await page.goto("http://127.0.0.1:13117/research-lab");
  await page.setViewportSize({ width: 1440, height: 1050 });
  const dataset = { base_currency: "USD", periods_per_year: 252, return_basis: "total_return", source_label: "Mock Data browser fixture", assets: [{ key: "A", ticker: "A", currency: "USD" }, { key: "B", ticker: "B", currency: "USD" }], observations: Array.from({ length: 20 }, (_, index) => ({ start_date: `2025-01-${String(index + 1).padStart(2, "0")}`, end_date: `2025-01-${String(index + 2).padStart(2, "0")}`, returns: { A: 0.01, B: -0.005 } })) };
  const allocation = page.getByRole("form", { name: "Portfolio allocation inputs", exact: true });
  await expect(allocation.getByLabel("Return dataset JSON", { exact: true })).toHaveValue("");
  await allocation.getByLabel("Return dataset JSON", { exact: true }).fill(JSON.stringify(dataset));
  await allocation.getByRole("button", { name: "Run portfolio allocation", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Saved allocation run #42" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Hypothetical allocation weights" }).getByText("50.00%")).toHaveCount(2);
  await page.getByText("Saved research runs", { exact: true }).click();
  await expect(page.getByRole("button", { name: "Open run 42", exact: true })).toBeEnabled();
  const runDownload = page.waitForEvent("download");
  await page.getByRole("link", { name: "Download saved inputs and result (JSON)" }).click();
  await (await runDownload).saveAs(resolve(output, "mock-data-run.json"));
  await page.getByRole("button", { name: "Rebalancing simulation", exact: true }).click();
  const simulation = page.getByRole("form", { name: "Rebalancing simulation inputs", exact: true });
  await simulation.getByLabel("Return dataset JSON", { exact: true }).fill(JSON.stringify(dataset));
  await simulation.getByLabel("Initial weights JSON", { exact: true }).fill('{"A":0.5,"B":0.5}');
  await simulation.getByLabel("Weight decision date", { exact: true }).fill("2024-12-31");
  await simulation.getByRole("button", { name: "Run rebalancing simulation", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Saved simulation run #43" })).toBeVisible();
  await expect(page.getByRole("img", { name: /Hypothetical wealth index/ })).toBeVisible();
  checks.push("blank explicit lab inputs, equal-weight request, saved metrics, actual success history state, JSON download and simulation chart");
  await page.getByText("Source and document adapters", { exact: true }).click();
  await page.getByLabel("Company for source evidence", { exact: true }).selectOption("7");
  await page.getByRole("button", { name: "Run sec annual facts", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Mock Data source · partial" })).toBeVisible();
  await page.getByText("Market, identity and calendar adapters", { exact: true }).click();
  await page.getByLabel("Data action", { exact: true }).selectOption("calendar");
  const calendar = page.getByRole("form", { name: "Exchange calendar adapter inputs", exact: true });
  await calendar.getByLabel("Requested start date", { exact: true }).fill("2025-01-01");
  await calendar.getByLabel("Requested end date", { exact: true }).fill("2025-01-10");
  await calendar.getByRole("button", { name: "Run exchange calendar", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Mock Data calendar · source response" })).toBeVisible();
  checks.push("explicit SEC and calendar actions, partial source receipt and document provenance links");
  await capture("research-lab-desktop");
  await page.setViewportSize({ width: 390, height: 844 });
  await capture("research-lab-mobile");
  assert.deepEqual(failures, []);
  await writeFile(resolve(output, "summary.json"), JSON.stringify({ classification: "Mock Data browser verification", backend_or_provider_calls: false, browser: "system Chromium", checks, page_errors: failures, post_paths: posts.map(post => post.path), screenshots: 5 }, null, 2));
  console.log(JSON.stringify({ passed: checks.length, checks, page_errors: failures }, null, 2));
} finally { await browser.close(); }
