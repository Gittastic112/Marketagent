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

const root = fileURLToPath(new URL("../", import.meta.url));
const nativeRequire = createRequire(import.meta.url);
function success(data: unknown): ApiResponse<unknown> {
  return {data, meta: {status: "success", source: "internal", is_stale: false, last_updated: null,
    warnings: [], confidence: "unknown", processing_time_ms: null}, errors: []};
}

// Render actual page output with only the request boundary replaced. This
// exercises successful-empty versus failed-envelope behavior, not source text.
async function pageHtml(relative: string, responseFor: (url: string) => ApiResponse<unknown>,
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
        serverFetchApi: async (url: string) => responseFor(url).data};
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
      : url.endsWith("/coverage") || url.endsWith("/identities") ? null : []));
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
