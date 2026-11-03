import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import test from "node:test";

const clientApiHelpers = [
  "fetchApi",
  "fetchApiResponse",
  "fetchOAuthStatus",
  "fetchEvidenceLedger",
  "fetchVariantPerceptions",
  "fetchDecisionLogs",
  "listValuationModels",
  "getValuationModelAssumptions",
  "fetchValuationContext",
  "listFinancialPeriods",
  "listExtractedFinancialCandidates",
  "listNormalizedSnapshots",
  "listAiOutputs",
  "listFilingSections",
  "fetchMarketQuote",
  "fetchFinancialTrends",
];

function pageFiles(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const entryPath = path.join(directory, entry.name);
    if (entry.isDirectory()) return pageFiles(entryPath);
    return entry.name === "page.tsx" ? [entryPath] : [];
  });
}

test("server-rendered pages do not use the cookie-blind client API helpers", () => {
  const offenders: string[] = [];
  for (const filePath of pageFiles(path.resolve("app"))) {
    const source = readFileSync(filePath, "utf8");
    if (/^\s*["']use client["'];/.test(source)) continue;

    for (const helper of clientApiHelpers) {
      if (new RegExp(`\\b${helper}\\b`).test(source)) {
        offenders.push(`${path.relative(process.cwd(), filePath)}: ${helper}`);
      }
    }
  }

  assert.deepEqual(offenders, []);
});

test("page proxy requires a NextAuth token while leaving API routes structured", () => {
  const source = readFileSync(path.resolve("proxy.ts"), "utf8");

  assert.match(source, /getToken\(\{ req: request, secret \}\)/);
  assert.match(source, /configurationError/);
  assert.match(source, /callbackUrl/);
  assert.match(source, /\(\?!api\|auth\/signin/);
});

test("local auth readiness is explicit and does not expose credential values", () => {
  const routeSource = readFileSync(path.resolve("app/api/auth/readiness/route.ts"), "utf8");
  const signInSource = readFileSync(path.resolve("app/auth/signin/page.tsx"), "utf8");

  assert.match(routeSource, /LOCAL_AUTH_USERNAME/);
  assert.match(routeSource, /LOCAL_AUTH_PASSWORD/);
  assert.match(routeSource, /NEXTAUTH_SECRET/);
  assert.doesNotMatch(routeSource, /process\.env\[[^\]]+\]\s*[),}]/);
  assert.match(signInSource, /\/api\/auth\/readiness/);
});

test("backend requests use signed internal identity instead of recursive session callbacks", () => {
  const serverApiSource = readFileSync(path.resolve("lib/server-api.ts"), "utf8");
  const backendProxySource = readFileSync(path.resolve("app/api/backend/[...path]/route.ts"), "utf8");
  const internalAuthSource = readFileSync(path.resolve("lib/internal-auth.ts"), "utf8");
  const nextConfigSource = readFileSync(path.resolve("next.config.mjs"), "utf8");

  assert.match(serverApiSource, /readServerIdentity\(secret\)/);
  assert.match(serverApiSource, /await connection\(\)/);
  assert.match(serverApiSource, /process\.env\["NEXTAUTH_SECRET"\]/);
  assert.match(serverApiSource, /process\.env\["API_BASE_URL"\]/);
  assert.match(serverApiSource, /createBackendAuthHeaders/);
  assert.match(serverApiSource, /AbortSignal\.timeout/);
  assert.doesNotMatch(serverApiSource, /\bCookie:/);
  assert.doesNotMatch(serverApiSource, /getServerSession/);
  assert.doesNotMatch(serverApiSource, /cache\(async/);
  assert.doesNotMatch(serverApiSource, /const SERVER_API_BASE_URL/);

  const serverAuthSource = readFileSync(path.resolve("lib/server-auth.ts"), "utf8");
  assert.match(serverAuthSource, /await cookies\(\)/);
  assert.match(serverAuthSource, /findNextAuthSessionToken/);
  assert.match(serverAuthSource, /decode\(\{ token: encryptedToken, secret \}\)/);
  assert.doesNotMatch(serverAuthSource, /console\.|logger\./);

  assert.match(backendProxySource, /getToken\(\{ req: request, secret \}\)/);
  assert.match(backendProxySource, /backendRequestHeaders\(request.headers\)/);
  assert.match(backendProxySource, /redirect: "error"/);
  assert.match(backendProxySource, /createBackendAuthHeaders/);
  assert.match(backendProxySource, /AbortSignal\.timeout/);
  assert.match(backendProxySource, /export async function PUT/);

  assert.match(internalAuthSource, /createHmac\("sha256"/);
  assert.match(internalAuthSource, /NEXTAUTH_SECRET/);
  assert.doesNotMatch(nextConfigSource, /api\/backend/);
});

test("company setup and SEC import expose resilient configured states", () => {
  const setupSource = readFileSync(path.resolve("components/company-setup-wizard.tsx"), "utf8");
  const companySource = readFileSync(path.resolve("app/companies/[id]/page.tsx"), "utf8");
  const dataSource = readFileSync(path.resolve("app/data/page.tsx"), "utf8");

  assert.match(setupSource, /fetchApiResponse<string\[\]>/);
  assert.match(setupSource, /industryWarnings/);
  assert.match(setupSource, /No Damodaran industry taxonomy is loaded/);

  assert.match(companySource, /CheckboxField/);
  assert.match(companySource, /SEC EDGAR.*automatic/);
  assert.doesNotMatch(companySource, /disabled=\{secSources\.length === 0\}/);

  assert.match(dataSource, /activeRssSources/);
  assert.match(dataSource, /preferredSecSource/);
  assert.match(dataSource, /secCompanies/);
  assert.match(dataSource, /SEC EDGAR \(automatic\)/);
  assert.doesNotMatch(dataSource, /id="sec-fetch-source-id"/);
});

test("dashboard creation links open the existing company and thesis forms", () => {
  const source = readFileSync(path.resolve("app/page.tsx"), "utf8");
  assert.match(source, /href="\/companies"[^>]*>Add Company/);
  assert.match(source, /href="\/thesis-notes"[^>]*>Write Thesis/);
  assert.doesNotMatch(source, /href="\/(?:companies|thesis-notes)\/new"/);
});

test("portfolio management separates opening balances, security activity, and cash activity", () => {
  const source = readFileSync(path.resolve("app/portfolio/manage/page.tsx"), "utf8");

  assert.match(source, /Set Opening Holding/);
  assert.match(source, /Record Security Activity/);
  assert.match(source, /Record Cash Activity/);
  assert.match(source, /name="ticker" type="hidden" value="CASH"/);
  assert.match(source, /name="price" type="hidden" value="0"/);
});

test("financial extraction actions use registered backend routes", () => {
  const actionsSource = readFileSync(path.resolve("app/actions/financials.ts"), "utf8");
  const adminSource = readFileSync(path.resolve("app/admin/damodaran/page.tsx"), "utf8");

  assert.match(actionsSource, /\/api\/filings\/\$\{filingId\}\/extract-financials/);
  assert.match(actionsSource, /\/api\/companies\/\$\{companyId\}\/extract-xbrl/);
  assert.doesNotMatch(actionsSource, /serverPostApi\(`\/filings\//);
  assert.doesNotMatch(actionsSource, /serverPostApi\(`\/companies\/\$\{companyId\}\/extract-xbrl/);
  assert.match(adminSource, /postFormApi\(`\/api\/admin\/damodaran\/import`/);
  assert.doesNotMatch(adminSource, /NEXT_PUBLIC_API_BASE_URL/);
});
