import assert from "node:assert/strict";
import { readFileSync, existsSync, statSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { test } from "node:test";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import ts from "typescript";
import { errorResponse, type ApiResponse } from "./api/contract.ts";
import type { DashboardOverview } from "./api/health.ts";
import type { PortfolioSnapshot } from "./api/portfolio.ts";

const root = fileURLToPath(new URL("../", import.meta.url));
const nativeRequire = createRequire(import.meta.url);
function success(data: unknown): ApiResponse<unknown> {
  return {data, meta: {status: "success", source: "internal", is_stale: false, last_updated: null,
    warnings: [], confidence: "unknown", processing_time_ms: null}, errors: []};
}

// Render actual page output with only the request boundary replaced. This
// exercises successful-empty versus failed-envelope behavior, not source text.
async function pageHtml(relative: string, responseFor: (url: string) => ApiResponse<unknown> & {httpStatus?: number},
  component?: {exportName: string; props: Record<string, unknown>},
  searchParams: Record<string, string | string[]> = {tab: "series"}) {
  const cache = new Map<string, any>();
  function load(relative: string): any {
    const candidate = path.resolve(root, relative);
    const file = [candidate, `${candidate}.tsx`, `${candidate}.ts`, `${candidate}/index.ts`, `${candidate}/index.tsx`]
      .find(file => existsSync(file) && statSync(file).isFile())!;
    if (cache.has(file)) return cache.get(file);
    const module = {exports: {} as any};
    cache.set(file, module.exports);
    const code = ts.transpileModule(readFileSync(file, "utf8"), {compilerOptions: {
      module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true,
    }}).outputText;
    const require = (name: string): any => {
      if (name === "server-only") return {};
      if (name === "@/lib/server-api") return {serverFetchApiResponse: async (url: string) => responseFor(url),
        serverPostApiResponse: async (url: string) => responseFor(url),
        serverFetchApi: async (url: string) => {
          const response = responseFor(url);
          if (response.errors.length || response.meta.status !== "success") {
            throw new (load("lib/api/contract").ApiError)(response.errors[0]?.message || "Request failed", response.httpStatus || 503);
          }
          return response.data;
        }};
      if (name === "@/app/actions") return new Proxy({}, {get: () => async () => undefined});
      if (name === "next/link") return {__esModule: true, default: ({href, children}: any) => createElement("a", {href}, children)};
      if (name === "next/navigation") return {notFound: () => {throw new Error("Not found");},
        useRouter: () => ({refresh() {}, push() {}, replace() {}}), useSearchParams: () => new URLSearchParams(), usePathname: () => "/test"};
      if (name === "@/components/providers/data-health-updater") return {DataHealthUpdater: () => null};
      return name.startsWith("@/") ? load(name.slice(2)) : name.startsWith(".") ? load(path.resolve(path.dirname(file), name)) : nativeRequire(name);
    };
    new Function("require", "module", "exports", code)(require, module, module.exports);
    return module.exports;
  }
  const page = component
    ? createElement(load(relative)[component.exportName], component.props)
    : await load(relative).default({params: Promise.resolve({id: "7"}), searchParams: Promise.resolve(searchParams)});
  return renderToStaticMarkup(page);
}

const company = {id: 7, name: "Mock Data company", ticker: "MOCK", market: "US"};

test("financial review plan renders source actions and keeps absent evidence distinct", async () => {
  const report = {basis: "Mock Data review", source_document_count: 1, generated_at: "2026-11-07T12:00:00Z", actions: [],
    periods: [{year: 2025, currency: "USD", report_date: null, source_linked_count: 1, checklist_count: 2, notes: [], fields: [
      {metric: "debt", label: "Debt", status: "recorded_with_source", action: "Inspect exact evidence", candidate_count: 1,
        source_links: [{candidate_id: 4, document_id: 3, href: "/documents/3/sections"}]},
      {metric: "cash", label: "Cash", status: "missing", action: "An absent disclosure is not zero", candidate_count: 0, source_links: []},
    ]}], limitations: []};
  const html = await pageHtml("components/financial-review-plan", () => success(null), {
    exportName: "FinancialReviewPlanPanel", props: {report, track: "operating", year: "2025"},
  });
  assert.match(html, /1 of 2 checklist items linked/);
  assert.match(html, /Source linked/); assert.match(html, /Find disclosure/);
  assert.match(html, /<th scope="row">/); assert.match(html, /<th scope="col">Input<\/th>/);
  assert.match(html, /href="\/documents\/3\/sections"/);
  assert.match(html, /Bank \/ financial-services equity/);
  assert.doesNotMatch(html, /NaN|undefined|100% complete/);
});

test("bottom-up macro results render partial coverage without a complete company estimate", async () => {
  const html = await pageHtml("components/macro/macro-results", () => success(null), {
    exportName: "BottomUpResult", props: {result: {
      method: "bottom_up", firm_value: {duration: null, cyclicality: 0, inflation_sensitivity: null, currency_sensitivity: null},
      metric_coverage: {duration: .6, cyclicality: 1}, covered_contributions: {duration: 1.2, cyclicality: 0},
      warnings: [], basis: "Mock Data segment values",
    }},
  });
  assert.match(html, /Not available/);
  assert.match(html, /60\.00%/);
  assert.match(html, /100\.00%/);
  assert.match(html, /<td>1\.2<\/td>/);
  assert.match(html, /covered contribution is a partial sum/);
  assert.doesNotMatch(html, /NaN|undefined/);
});

test("macro top-down form supports labeled expanded history without inventing values", async () => {
  const html = await pageHtml("components/macro/macro-top-down-form", () => success(null), {
    exportName: "MacroTopDownForm", props: {market: "IN", country: "India", sic: "", values: {period_count: "9"}},
  });
  assert.match(html, /Period 9 label/);
  assert.match(html, /for="macro-gdp_growth-9"/);
  assert.match(html, /Update period count/);
  assert.doesNotMatch(html, /placeholder="Operating income"/);
});

test("macro assumption tabs do not label entered values as facts or show an expanded warning wall", async () => {
  const html = await pageHtml("app/macro/page", () => success([]), undefined, {tab:"top-down"});
  assert.match(html, /User Assumption/);
  assert.doesNotMatch(html, />Fact<|mutate DCF/);
  assert.match(html, /<details[^>]*><summary>How to interpret macro results<\/summary>/);
});

test("macro workbench consumes canonical bottom-up result and preserves invalid form entries", async () => {
  let posts = 0;
  const result = {method: "bottom_up", firm_value: {duration: 0, cyclicality: null},
    operating_income: {}, metric_coverage: {duration: 1}, covered_contributions: {duration: 0}, warnings: []};
  const response = (url: string) => {
    if (url === "/api/valuation/macro/bottom-up") { posts++; return success(result); }
    return success([]);
  };
  const html = await pageHtml("app/macro/page", response, undefined, {
    tab: "bottom-up", run: "bottom-up", segment_1_name: "Mock Data", segment_1_sic: "1234", segment_1_value: "100",
  });
  assert.equal(posts, 1);
  assert.match(html, /Bottom-up sensitivity coverage/);
  assert.match(html, /100\.00%/);
  const invalid = await pageHtml("app/macro/page", response, undefined, {
    tab: "bottom-up", run: "bottom-up", segment_1_name: "Mock Data", segment_1_sic: "1234", segment_1_value: "",
  });
  assert.equal(posts, 1, "Incomplete inputs must not be sent as zeros");
  assert.match(invalid, /Enter a finite number for segment 1 value/);
  assert.match(invalid, /value="Mock Data"/);
});

test("macro transport and calculation failures render recoverable errors on the selected tab", async () => {
  for (const tab of ["sector", "bottom-up"]) {
    const html = await pageHtml("app/macro/page", url => url.includes("/valuation/macro/")
      ? errorResponse("NETWORK_ERROR", "Mock Data calculation unavailable") : success([]), undefined, {
      tab, sic:"1234", run:tab, segment_1_name:"Mock Data",segment_1_sic:"1234",segment_1_value:"100",
    });
    assert.match(html, /Mock Data calculation unavailable/);
    assert.doesNotMatch(html, /Enter one or more SIC-backed segments|Select a market and SIC|macro benchmark is not available/);
  }
});

function dashboardData(snapshot: PortfolioSnapshot | null): DashboardOverview {
  return {companies: [], events: [], alerts: [], thesis_notes: [], processing_runs: [], portfolio_analytics: null,
    default_portfolio: {id: 41, name: "Mock Data portfolio", base_currency: "USD", description: null},
    default_portfolio_snapshot: snapshot,
    daily_brief: {summary: "Mock Data stored preview", calculation_status: "complete", valuation_analysis_status: "not_run",
      contradiction_analysis_status: "not_run", last_reviewed_at: null, new_since_last_review: {filings: [], portfolio_moves: []},
      high_materiality_events: [], thesis_contradictions: [], thesis_confirmations: [], valuation_relevance: [],
      processing_failures: [], inspection_queue: [], warnings: [], contains_mock_data: true, contains_stale_data: false,
      source_event_ids: [], source_raw_document_ids: [], source_market_price_ids: [], source_alert_ids: []}};
}

test("dashboard incomplete snapshot names exact price and FX gaps within the portfolio link", async () => {
  for (const calculation_status of ["partial", "not_available"] as const) {
    const snapshot: PortfolioSnapshot = {id: 42, portfolio_id: 41, snapshot_date: "2026-11-04",
      total_market_value: null, total_cost_basis: null, total_cash: 0, total_portfolio_value: null,
      base_currency: "USD", calculation_status, holdings_count: 4, priced_holdings_count: 2,
      missing_price_tickers_json: ["MISSING-US", "MISSING-IN"], missing_fx_pairs_json: ["INR/USD"],
      payload_json: null, created_at: "2026-11-04T12:00:00Z"};
    const html = await pageHtml("app/page", url => {
      assert.equal(url, "/dashboard/overview");
      return success(dashboardData(snapshot));
    });
    const card = html.match(/<a href="\/portfolio\/41">([\s\S]*?)<\/a>/)?.[1];
    assert.ok(card, "Missing-input guidance must navigate to the affected portfolio");
    assert.match(card, /2 of 4 holdings priced\./);
    assert.match(card, /Prices needed: MISSING-US, MISSING-IN\./);
    assert.match(card, /FX rates needed: INR\/USD\./);
    assert.match(card, /Open portfolio to review missing inputs\./);
    assert.match(card, /Not available/);
    assert.match(card, /Stored snapshot · 2026-11-04/);
    assert.doesNotMatch(card, /\$0\.00/);
  }
});

test("dashboard complete and valid zero snapshots never claim missing inputs", async () => {
  for (const value of [0, 125]) {
    const snapshot: PortfolioSnapshot = {id: 42, portfolio_id: 41, snapshot_date: "2026-11-04",
      total_market_value: value, total_cost_basis: value, total_cash: 0, total_portfolio_value: value,
      base_currency: "USD", calculation_status: "complete", holdings_count: value === 0 ? 0 : 2,
      priced_holdings_count: value === 0 ? 0 : 2, missing_price_tickers_json: [], missing_fx_pairs_json: [],
      payload_json: null, created_at: "2026-11-04T12:00:00Z"};
    const html = await pageHtml("app/page", () => success(dashboardData(snapshot)));
    const card = html.match(/<a href="\/portfolio\/41">([\s\S]*?)<\/a>/)?.[1];
    assert.ok(card);
    assert.match(card, value === 0 ? /\$0\.00/ : /\$125\.00/);
    assert.match(card, /Stored snapshot · 2026-11-04/);
    assert.doesNotMatch(card, /holdings priced|Prices needed|FX rates needed|review missing inputs|Not available/);
  }
  const absent = await pageHtml("app/page", () => success(dashboardData(null)));
  const card = absent.match(/<a href="\/portfolio\/41">([\s\S]*?)<\/a>/)?.[1];
  assert.ok(card);
  assert.match(card, /Capture a priced snapshot/);
  assert.doesNotMatch(card, /holdings priced|Prices needed|FX rates needed|review missing inputs/);
});

test("company overview keeps failed collections unavailable and preserves loaded evidence", async () => {
  const document = {id: 21, company_id: 7, title: "Mock Data retained filing", document_type: "manual", source_id: 2, content_hash: "mock-hash"};
  const html = await pageHtml("app/companies/[id]/page", url => url === "/companies" ? success([{...company, cik: "0000000007", exposure_tags: []}])
    : url === "/raw-documents/summaries" ? success([document])
    : url === "/api/market/quote?ticker=MOCK&market=US" ? success(null)
    : url === "/companies/7/financial-periods" || url.startsWith("/company-research/profiles") ? success([])
    : {...errorResponse("NETWORK_ERROR", "Mock Data collection outage"), data: [{id: 999, company_id: 7, title: "Untrusted failed payload"}]});
  for (const label of ["Events could not be loaded", "Alerts could not be loaded", "Thesis notes could not be loaded", "Exposure tags could not be loaded", "Filing sources could not be loaded"]) assert.match(html, new RegExp(label));
  assert.match(html, /Mock Data retained filing/);
  assert.match(html, /href="\/companies\/7"[^>]*>Try again/);
  assert.doesNotMatch(html, /No linked events|No active alerts|No linked thesis notes|Untrusted failed payload/);
  for (const label of ["Recorded activity", "Recorded alerts", "Thesis"]) {
    assert.match(html, new RegExp(`${label}<\\/div><div class="metric-value">Unavailable<`));
  }
  assert.match(html, /Documents<\/div><div class="metric-value">1</);
});

test("company overview successful empty collections stay empty and failed documents do not become zero", async () => {
  const loaded = await pageHtml("app/companies/[id]/page", url => success(url === "/companies" ? [{...company, exposure_tags: []}]
    : url.startsWith("/api/market/quote") ? null : []));
  for (const text of [/No linked documents/, /No linked events/, /No active alerts/, /No linked thesis notes/]) assert.match(loaded, text);
  assert.match(loaded, /Recorded activity<\/div><div class="metric-value">0</);
  assert.match(loaded, /Thesis<\/div><div class="metric-value">None</);
  const failed = await pageHtml("app/companies/[id]/page", url => url === "/raw-documents/summaries"
    ? errorResponse("NETWORK_ERROR", "Mock Data document outage")
    : success(url === "/companies" ? [{...company, exposure_tags: []}] : url.startsWith("/api/market/quote") ? null : []));
  assert.match(failed, /Documents could not be loaded/);
  assert.match(failed, /Documents<\/div><div class="metric-value">Unavailable</);
  assert.doesNotMatch(failed, /No linked documents/);
});

test("company overview distinguishes unavailable identity from a missing company", async () => {
  for (const response of [errorResponse("NETWORK_ERROR", "Mock Data identity outage"), success(null)]) {
    const unavailable = await pageHtml("app/companies/[id]/page", () => response);
    assert.match(unavailable, /Company records could not be loaded/);
    assert.match(unavailable, /href="\/companies\/7"[^>]*>Try again/);
    assert.doesNotMatch(unavailable, /No company exists/);
  }
  const missing = await pageHtml("app/companies/[id]/page", () => success([]));
  assert.match(missing, /No company exists for this ID/);
});

test("valuation identity transport failures are recoverable while actual 404 stays not found", async () => {
  const unavailable = await pageHtml("app/companies/[id]/valuation/page", () => errorResponse("NETWORK_ERROR", "Mock Data identity outage"));
  assert.match(unavailable, /Company information could not be loaded/);
  assert.match(unavailable, /href="\/companies\/7\/valuation"[^>]*>Try again/);
  assert.match(unavailable, /href="\/companies"/);
  assert.doesNotMatch(unavailable, /No valuation models yet|0 models/);
  await assert.rejects(pageHtml("app/companies/[id]/valuation/page", () => ({
    ...errorResponse("NOT_FOUND", "Company not found"), httpStatus: 404,
  })), /Not found/);
});

test("valuation failed model loading preserves available context without claiming zero models", async () => {
  const html = await pageHtml("app/companies/[id]/valuation/page", url => url === "/companies/7" ? success(company)
    : url.includes("/context/") ? success({market: "US", country: "United States", default_currency: "USD", recommended_benchmark_country: "United States", warnings: []})
    : errorResponse("NETWORK_ERROR", "Mock Data models outage"));
  assert.match(html, /Models unavailable/);
  assert.match(html, /Could not load valuation models/);
  assert.match(html, /United States/);
  assert.match(html, /href="\/companies\/7\/valuation"[^>]*>Try again/);
  assert.match(html, /Create Valuation Model/);
  assert.doesNotMatch(html, /0 models|No valuation models yet/);
});

test("valuation context failure preserves saved models and successful empty models stay empty", async () => {
  const model = {id: 31, name: "Mock Data retained model", model_type: "fcff", readiness: "calculated",
    readiness_detail: "Mock Data calculated estimate", intrinsic_value_per_share: 10, cash_flow_currency: "INR", assumption_set_count: 1};
  const html = await pageHtml("app/companies/[id]/valuation/page", url => url === "/companies/7" ? success(company)
    : url.endsWith("valuation-model-summaries") ? success([model]) : errorResponse("NETWORK_ERROR", "Mock Data context outage"));
  assert.match(html, /Market context could not be loaded/);
  assert.match(html, /Mock Data retained model/);
  assert.match(html, /1 model/);
  assert.match(html, /href="\/companies\/7\/valuation\/31"/);
  assert.match(html, /Review company setup/);
  assert.doesNotMatch(html, /Not Configured|0 models|No valuation models yet/);
  const empty = await pageHtml("app/companies/[id]/valuation/page", url => success(url === "/companies/7" ? company
    : url.endsWith("valuation-model-summaries") ? [] : {market: "US", country: "United States", default_currency: "USD", warnings: []}));
  assert.match(empty, /0 models/);
  assert.match(empty, /No valuation models yet/);
  assert.doesNotMatch(empty, /Models unavailable|Could not load valuation models/);
});

test("data health failures remain unavailable instead of empty results or healthy zero counts", async () => {
  const html = await pageHtml("app/data-health/page", () => errorResponse("NETWORK_ERROR", "Mock Data outage"));
  for (const message of ["Processing runs could not be loaded", "Provider health could not be loaded",
    "Sources could not be loaded", "Contradiction alerts could not be loaded"]) assert.match(html, new RegExp(message));
  assert.doesNotMatch(html, /No unreviewed contradictions found|No sources configured|No processing runs recorded|0 runs tracked/);
  assert.match(html, /Runs unavailable/);
});

test("data health preserves successful empty states and discloses its recent-run scope", async () => {
  const html = await pageHtml("app/data-health/page", url =>
    url === "/api/readiness" || url.startsWith("/data-health/peer-review-receipts")
      ? errorResponse("NETWORK_ERROR", "Mock Data unavailable check") : success([]));
  assert.match(html, /No unreviewed contradictions found/);
  assert.match(html, /No sources configured/);
  assert.match(html, /No processing runs recorded/);
  assert.match(html, /latest 100 runs/);
  assert.doesNotMatch(html, /across the current local database|Processing runs could not be loaded/);
});

test("a failed evidence audit is unavailable, not an audit that was never requested", async () => {
  const html = await pageHtml("app/data-health/page", () => errorResponse("NETWORK_ERROR", "Mock Data audit failure"),
    undefined, {audit: "evidence"});
  assert.match(html, /Evidence integrity report is unavailable/);
  assert.match(html, /Unavailable/);
  assert.doesNotMatch(html, /health-metric-value[^>]*>Not run/);
});

test("data health does not render stale payloads from failed envelopes", async () => {
  const html = await pageHtml("app/data-health/page", url => url === "/sources"
    ? {...errorResponse("NETWORK_ERROR", "Mock Data failure"), data: [{id: 1, name: "Untrusted leftover source"}]}
    : errorResponse("NETWORK_ERROR", "Mock Data unavailable"));
  assert.match(html, /Sources could not be loaded/);
  assert.doesNotMatch(html, /Untrusted leftover source/);
});

test("populated health tables preserve source links, provider failures, run bounds and partial errors", async () => {
  const runs = Array.from({length: 100}, (_, index) => ({id: index + 1, run_type: "Mock Data run",
    source_id: 1, source_type: "mock", status: "success", fetched_count: 3, created_count: 2,
    skipped_duplicate_count: 1, error_count: 0, started_at: "2026-10-01T12:00:00Z", finished_at: null}));
  const html = await pageHtml("app/data-health/page", url => {
    const data = url === "/processing-runs" ? runs : url === "/sources" ? [
      {id: 1, name: "Mock Data source", source_type: "manual", active: true, reliability_score: 0},
      {id: 2, name: "Mock Data older source", source_type: "manual", active: false, reliability_score: null},
    ] : url === "/api/providers/health" ? [{provider_name: "Mock Data provider", capability: "prices", market: "US",
      requirement_level: "core", status: "failing", freshness_label: "Unavailable", recent_run_count: 2,
      consecutive_failures: 2, last_failure_at: "2026-10-01T12:00:00Z", failure_reason: "Mock Data timeout"}]
      : url === "/alerts" ? [{id: 17, company_id: 7, alert_type: "contradiction", review_status: "unreviewed",
        title: "Mock Data contradiction", summary: "Review the source"}] : null;
    return data ? {...success(data), meta: {...success(data).meta, is_mock: true}} : errorResponse("NETWORK_ERROR", "Mock Data partial failure");
  });
  assert.match(html, /Mock Data provider/);
  assert.match(html, /2 consecutive failures/);
  assert.match(html, /Mock Data timeout/);
  assert.match(html, /href="\/alerts\/17"/);
  assert.match(html, /No runs in recent window/);
  assert.match(html, /300 records fetched in this window/);
  assert.match(html, /Data health rows are mocked/);
  assert.match(html, /Requested health summaries could not be loaded/);
  assert.equal((html.match(/<strong>Mock Data run<\/strong>/g) || []).length, 26); // one type row + 25 recent runs
  assert.doesNotMatch(html, /Provider health could not be loaded|Processing runs could not be loaded/);
});

test("source health keeps available source rows visible when run history fails", async () => {
  const html = await pageHtml("app/data-health/page", url => url === "/sources"
    ? success([{id: 1, name: "Mock Data available source", source_type: "manual", active: true}])
    : errorResponse("NETWORK_ERROR", "Mock Data unavailable history"));
  assert.match(html, /Mock Data available source/);
  assert.match(html, /Runs unavailable/);
  assert.doesNotMatch(html, /No runs in recent window/);
});

test("market prices bound rendered rows and preserve the ticker across page links", async () => {
  const requests: string[] = [];
  const prices = Array.from({length: 51}, (_, index) => ({id: index + 1, company_id: 7,
    ticker: "MOCK", price: 10, currency: "USD", as_of_date: "2026-07-01", warnings: []}));
  const html = await pageHtml("app/market-prices/page", url => {
    requests.push(url);
    return success(url.startsWith("/market-prices") ? prices : [company]);
  }, undefined, {page: "2", ticker: " mock "});
  const query = new URL(requests.find(url => url.startsWith("/market-prices"))!, "http://local.invalid").searchParams;
  assert.equal(query.get("limit"), "51");
  assert.equal(query.get("offset"), "50");
  assert.equal(query.get("ticker"), "MOCK");
  assert.equal((html.match(/<form[^>]*aria-label="Update market price"/g) || []).length, 50);
  assert.doesNotMatch(html, /id="price-price-51"/);
  assert.match(html, /Page 2/);
  assert.match(html, /href="\/market-prices\?ticker=MOCK&amp;page=1"/);
  assert.match(html, /href="\/market-prices\?ticker=MOCK&amp;page=3"/);
});

test("market-price invalid pages fall back safely and beyond-end pages remain navigable", async () => {
  for (const value of ["-1", "2002", "NaN", "1.5"]) {
    let request = "";
    await pageHtml("app/market-prices/page", url => {
      if (url.startsWith("/market-prices")) request = url;
      return success([]);
    }, undefined, {page: value});
    assert.equal(new URL(request, "http://local.invalid").searchParams.get("offset"), "0");
  }
  const empty = await pageHtml("app/market-prices/page", () => success([]), undefined, {page: "3"});
  assert.match(empty, /No prices on this page/);
  assert.match(empty, /Previous page/);
  assert.doesNotMatch(empty, />Next page</);
});

const cases = [
  ["app/research/page", /Documents could not be loaded/, /No documents ingested yet/],
  ["app/intelligence/review/page", /Review queue could not be loaded/, /No explicit contradictions/],
  ["app/companies/[id]/evidence/page", /Evidence could not be loaded/, /No evidence items logged/],
  ["app/narratives/page", /Narratives could not be loaded/, /No narratives being tracked/],
  ["app/sources/page", /Sources could not be loaded/, /No sources yet/],
  ["app/documents/page", /Documents could not be loaded/, /No raw documents yet/],
  ["app/thesis-notes/page", /Thesis notes could not be loaded/, /No thesis notes yet/],
  ["app/social/page", /Social posts could not be loaded/, /No social posts imported yet/],
  ["app/market-prices/page", /Market prices could not be loaded/, /No market prices yet/],
  ["app/events/page", /Events could not be loaded/, /No events yet/],
  ["app/alerts/page", /Alerts could not be loaded/, /No alerts yet/],
  ["app/portfolio/manage/page", /Portfolios could not be loaded/, /No portfolios yet/],
] as const;
for (const [page, failed, empty] of cases) test(`${page} keeps failure distinct from successful empty records`, async () => {
  const failure = await pageHtml(page, url => url === "/companies/7" ? success(company) : errorResponse("NETWORK_ERROR", "Mock Data connection failure"));
  assert.match(failure, failed);
  assert.doesNotMatch(failure, empty);
  const loaded = await pageHtml(page, url => success(url === "/companies/7" ? company : []));
  assert.match(loaded, empty);
  assert.doesNotMatch(loaded, failed);
});

test("research retains available documents while failed event and thesis panels stay unavailable", async () => {
  const html = await pageHtml("app/research/page", url => url === "/raw-documents/summaries"
    ? success([{id: 3, title: "Mock Data retained source", document_type: "manual", url: null}])
    : errorResponse("NETWORK_ERROR", "Mock Data failure"));
  assert.match(html, /Mock Data retained source/);
  assert.match(html, /Events could not be loaded/);
  assert.match(html, /Thesis notes could not be loaded/);
  assert.doesNotMatch(html, /No events extracted|No thesis notes recorded/);
});

test("narrative claims and mentions do not become zero records after a failed request", async () => {
  const html = await pageHtml("app/narratives/page", url => url === "/narrative-clusters"
    ? success([{id: 3, name: "Mock Data narrative", description: null, created_at: "2026-01-01"}])
    : errorResponse("NETWORK_ERROR", "Mock Data failure"));
  assert.match(html, /Claims could not be loaded/);
  assert.match(html, /Mentions could not be loaded/);
  assert.doesNotMatch(html, /No claims recorded|No mentions linked|>0 claims<|>0 mentions</);
});

test("fundamental source failures never become missing financial coverage", async () => {
  const html = await pageHtml("app/companies/[id]/fundamentals/page", url => url === "/companies/7"
    ? success(company) : errorResponse("NETWORK_ERROR", "Mock Data failure"));
  for (const text of [/Financial periods could not be loaded/, /Financial candidates could not be loaded/, /Normalized metrics could not be loaded/]) assert.match(html, text);
  assert.doesNotMatch(html, /No financial periods found|No candidates found|No normalized snapshots/);
});

test("financial reconciliation needs actual comparable metrics before claiming a match", async () => {
  for (const exactCount of [0, 1]) {
    const html = await pageHtml("app/companies/[id]/fundamentals/page", url => success(url === "/companies/7" ? company
      : url.endsWith("/reconciliation") ? {periods:exactCount ? [{period_id:1, year:2025, period_type:"annual", items:[{status:"exact", metric_code:"revenue", source_value:100, normalized_value:100}]}] : [],
        exact_count:exactCount, mismatch_count:0, normalized_only_count:0, missing_normalized_count:0}
      : url.endsWith("/coverage") || url.endsWith("/identities") || url.includes("/review-plan?") ? null : []));
    if (exactCount === 0) {
      assert.match(html, /No comparable reviewed metrics are available/);
      assert.doesNotMatch(html, /All comparable source metrics match/);
    } else {
      assert.match(html, /All comparable source metrics match/);
      assert.doesNotMatch(html, /No comparable reviewed metrics are available/);
    }
  }
});

test("failed provider health cannot claim FRED is unconfigured", async () => {
  const html = await pageHtml("app/macro/page", () => errorResponse("NETWORK_ERROR", "Mock Data failure"));
  assert.match(html, /FRED configuration could not be checked/);
  assert.match(html, /Macro series could not be loaded/);
  assert.doesNotMatch(html, /FRED Integration Not Configured/);
});

test("portfolio return cards distinguish selected-period TWR from annualized MWR and use their returned dates", async () => {
  for (const firstFlowDate of ["2026-01-01", null]) {
    const returnMetric = {calculation_status: "complete", return_decimal: 0, end_date: "2026-08-10", warnings: []};
    const html = await pageHtml("components/portfolio-performance-panel", () => success(null), {
      exportName: "PortfolioPerformancePanel",
      props: {
        snapshots: [
          {calculation_status: "complete", payload_json: null},
          {calculation_status: "complete", payload_json: null},
        ],
        startDate: "2026-07-20", endDate: "2026-08-10",
        performance: {
          time_weighted_return: {...returnMetric, start_date: "2026-07-20"},
          money_weighted_return: {...returnMetric, start_date: firstFlowDate},
        },
        attribution: {base_currency: "USD", confidence: "high", formula: "Mock Data attribution",
          blockers: [], warnings: [], holdings: [], source_snapshot_ids: [], source_transaction_ids: []},
        opportunityCost: null,
      },
    });
    assert.match(html, /TWR: selected period \(complete\)/);
    assert.match(html, /Period: 2026-07-20 to 2026-08-10\. Not annualized\./);
    assert.match(html, /MWR: annualized \(complete\)/);
    assert.ok(html.includes(`Since first cash flow: ${firstFlowDate || "Not available"} to 2026-08-10.`));
    assert.doesNotMatch(html, /Since first cash flow: 2026-07-20/);
    assert.equal((html.match(/>0\.00%</g) || []).length, 2);
  }
});
