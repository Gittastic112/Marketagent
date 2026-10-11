import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import test from "node:test";

const frontendRoot = fileURLToPath(new URL("../", import.meta.url));
const repositoryRoot = process.env.REPOSITORY_ROOT || path.join(frontendRoot, "..");

function readFrontendFile(filePath: string): string {
  return readFileSync(path.join(frontendRoot, filePath), "utf8");
}

function readRepositoryFile(filePath: string): string {
  return readFileSync(path.join(repositoryRoot, filePath), "utf8");
}

test("frontend utility compiler and project tokens are wired", () => {
  const postcss = readFrontendFile("postcss.config.mjs");
  const styles = readFrontendFile("app/globals.css");

  assert.match(postcss, /@tailwindcss\/postcss/);
  assert.match(styles, /^@import "tailwindcss";/);
  assert.match(styles, /--color-canvas:/);
  assert.match(styles, /--color-border-default:/);
  assert.match(styles, /--font-family-sans:/);
  assert.doesNotMatch(styles, /fonts\.googleapis\.com/);
});


test("Docker defaults to a bounded production runtime with an explicit development override", () => {
  const compose = readRepositoryFile("docker-compose.yml");
  const e2eCompose = readRepositoryFile("docker-compose.e2e.yml");
  const browserWorkflow = readRepositoryFile("scripts/run_browser_workflows.sh");
  const developmentCompose = readRepositoryFile("docker-compose.dev.yml");
  const testCompose = readRepositoryFile("docker-compose.test.yml");
  const dockerfile = readFrontendFile("Dockerfile");
  const nextConfig = readFrontendFile("next.config.mjs");
  const frontendDockerignore = readFrontendFile(".dockerignore");
  const rootDockerignore = readRepositoryFile(".dockerignore");

  assert.doesNotMatch(compose, /npm ci|npm run dev|--reload/);
  assert.match(compose, /target: runner/);
  assert.match(compose, /profiles: \["admin"\]/);
  assert.match(compose, /max-size: "10m"/);
  assert.match(compose, /condition: service_healthy/);
  assert.match(developmentCompose, /npm run dev/);
  assert.match(developmentCompose, /--reload/);
  assert.match(developmentCompose, /frontend_node_modules:\/app\/node_modules/);
  assert.match(testCompose, /name: market-intelligence-tests/);
  assert.match(testCompose, /network_mode: none/);
  assert.match(testCompose, /sqlite\+pysqlite:\/\/\/\/tmp\/isolated-test-default\.sqlite/);
  assert.match(testCompose, /\.\/data:\/workspace\/data:ro/);
  assert.doesNotMatch(testCompose, /env_file:|ports:|depends_on:|postgresql\+/);
  assert.match(developmentCompose, /frontend_next_cache:\/app\/\.next/);
  assert.match(dockerfile, /FROM base AS builder/);
  assert.match(dockerfile, /FROM node:24-slim AS runner/);
  assert.match(dockerfile, /\.next\/standalone/);
  assert.match(nextConfig, /output: "standalone"/);
  assert.match(rootDockerignore, /^\*\*$/m);
  for (const directory of ["data", "docs", "frontend", "damodaran_knowledge_base_v1"]) {
    assert.doesNotMatch(rootDockerignore, new RegExp(`^!${directory}(?:/|$)`, "m"));
  }
  assert.match(rootDockerignore, /^\*\*\/\.env$/m);
  assert.match(rootDockerignore, /^\*\*\/\.env\.\*$/m);
  assert.match(frontendDockerignore, /^\.env$/m);
  assert.match(frontendDockerignore, /^\.env\.\*$/m);
  assert.match(frontendDockerignore, /^!\.env\.example$/m);
  assert.match(e2eCompose, /E2E_BACKEND_PORT:-18000/);
  assert.match(e2eCompose, /E2E_FRONTEND_PORT:-13000/);
  assert.match(browserWorkflow, /E2E_BACKEND_PORT="\$\{E2E_BACKEND_PORT:-18000\}"/);
  assert.match(browserWorkflow, /E2E_FRONTEND_PORT="\$\{E2E_FRONTEND_PORT:-13000\}"/);
  assert.match(browserWorkflow, /Port %s is already allocated/);
  assert.match(browserWorkflow, /\/api\/readiness/);
  assert.doesNotMatch(browserWorkflow, /E2E_BACKEND_PORT\}\/api\/health/);
});


test("navigation and company route infrastructure are centralized", () => {
  const sidebar = readFrontendFile("components/sidebar.tsx");
  const companyLayout = readFrontendFile("app/companies/[id]/layout.tsx");
  const styles = readFrontendFile("app/globals.css");

  for (const group of ["Today", "Portfolio", "Research", "Data", "System"]) {
    assert.match(sidebar, new RegExp(`label: "${group}"`));
  }
  assert.match(sidebar, /prefetch=\{false\}/);
  assert.match(readFrontendFile("components/company-tabs.tsx"), /prefetch=\{false\}/);
  assert.match(companyLayout, /<CompanyTabs companyId=\{id\}/);
  assert.match(styles, /\.sidebar\.sidebar-open/);
  assert.match(styles, /\.company-tabs/);
});

test("company workspace typography and layout do not force page-level horizontal scrolling", () => {
  const detail = readFrontendFile("app/companies/[id]/page.tsx");
  const wizard = readFrontendFile("components/company-setup-wizard.tsx");
  const page = readFrontendFile("components/page.tsx");
  const styles = readFrontendFile("app/globals.css");

  assert.match(detail, /company-overview-header/);
  assert.match(detail, /company-overview-grid/);
  assert.match(detail, /company-event-card/);
  assert.match(detail, /privacy-consent/);
  assert.doesNotMatch(detail, /gridTemplateColumns: "1fr 1fr"/);
  assert.doesNotMatch(detail, />Decision Intelligence<|>Fundamentals<|>Valuation<\/Link>/);
  assert.match(wizard, /company-setup-steps/);
  assert.match(wizard, /responsive-field-row/);
  assert.doesNotMatch(wizard, /maxWidth: "600px"/);
  assert.match(page, /page-header-title-row/);
  assert.match(styles, /table \{[\s\S]*?min-width: 100%/);
  assert.doesNotMatch(styles, /table \{[\s\S]{0,100}min-width: 760px/);
  assert.match(styles, /\.table-wrap \{[\s\S]*?max-width: 100%/);
  assert.match(styles, /\.company-tabs \{[\s\S]*?flex-wrap: wrap/);
  assert.match(styles, /overflow-wrap: anywhere/);
});

test("responsive route matrix enforces readable typography", () => {
  const spec = readFrontendFile("e2e/accessibility-responsive.spec.ts");
  const timeline = readFrontendFile("components/events-timeline.tsx");
  const workspace = readFrontendFile("components/advanced-workspace.tsx");
  const diagnostics = readFrontendFile("components/valuation/diagnostic-panel.tsx");
  assert.match(spec, /collectTypographyFailures/);
  assert.match(spec, /Body text is \$\{bodySize\}px; expected at least 15px/);
  assert.match(spec, /Page title is \$\{titleSize\}px; expected 26–40px/);
  assert.match(spec, /fontSize\(element\) < 12/);
  assert.match(spec, /typography failures/);
  assert.match(spec, /ROUTE_READY_BUDGET_MS = 15_000/);
  assert.match(spec, /must render within the route-ready budget/);
  assert.doesNotMatch(timeline, /fontSize: "0\.7rem"/);
  assert.doesNotMatch(workspace, /fontSize: "0\.7rem"/);
  assert.doesNotMatch(diagnostics, /fontSize: "0\.7rem"/);
});

test("slow workspaces avoid sequential and per-record request waterfalls", () => {
  const narratives = readFrontendFile("app/narratives/page.tsx");
  const macro = readFrontendFile("app/macro/page.tsx");

  assert.match(narratives, /claimsRes, mentionsRes/);
  assert.match(narratives, /claimsByCluster/);
  assert.doesNotMatch(narratives, /clusters\.map\(async/);
  assert.match(macro, /seriesListRes, providerHealthRes/);
  assert.doesNotMatch(macro, /let fredConfigured = false;[\s\S]*?try/);
});

test("high-fanout and explicit diagnostic links do not prefetch expensive work", () => {
  const guardedFiles = [
    "components/topbar.tsx",
    "app/data-health/page.tsx",
    "app/companies/page.tsx",
    "app/portfolio/page.tsx",
    "app/valuation/page.tsx",
    "app/research/page.tsx",
    "app/page.tsx",
  ];
  for (const file of guardedFiles) {
    assert.match(readFrontendFile(file), /prefetch=\{false\}/, file);
  }
  const dataHealth = readFrontendFile("app/data-health/page.tsx");
  assert.doesNotMatch(dataHealth, /<Link(?![^>]*prefetch=\{false\})[^>]*href="\/data-health\?audit=/);
});


test("production workflows do not use blocking browser dialogs", () => {
  const workflowFiles = [
    "components/advanced-workspace.tsx",
    "components/financial-candidate-review.tsx",
    "components/valuation/autofill-draft-review.tsx",
    "components/valuation/valuation-change-log-panel.tsx",
    "app/admin/damodaran/page.tsx",
  ];
  for (const path of workflowFiles) {
    const source = readFrontendFile(path);
    assert.doesNotMatch(source, /\b(?:window\.)?(?:alert|confirm)\s*\(/, path);
  }
});


test("dashboard uses the consolidated overview endpoint", () => {
  const dashboard = readFrontendFile("app/page.tsx");
  assert.match(dashboard, /serverFetchApiResponse<DashboardOverview>\("\/dashboard\/overview"/);
  assert.match(dashboard, /timeoutMs: 30_000/);
  for (const legacyPath of ["/companies", "/events", "/alerts", "/thesis-notes", "/processing-runs"]) {
    assert.doesNotMatch(dashboard, new RegExp(`serverFetchApiResponse[^\\n]+${legacyPath}`));
  }
  assert.match(dashboard, /<DataStateNotices/);
  assert.match(dashboard, /metas=\{\[overviewRes\.meta\]\}/);
  assert.match(dashboard, /snapshot\.snapshot_date/);
  assert.match(dashboard, /portfolio \? "Capture a priced snapshot" : "Set up a portfolio"/);
  assert.match(dashboard, /formatCurrency\(snapshot.total_portfolio_value, snapshot.base_currency/);
  assert.match(dashboard, /if \(!overview\).*ErrorState/);
});

test("research routes use parallel requests and responsive layouts", () => {
  const brief = readFrontendFile("app/daily-brief/page.tsx");
  const research = readFrontendFile("app/research/page.tsx");
  const narratives = readFrontendFile("app/narratives/page.tsx");
  const styles = readFrontendFile("app/globals.css");

  assert.match(brief, /const \[briefRes, savedBriefsRes, scheduleRes\] = await Promise\.all/);
  assert.match(brief, /className="brief-comparison-grid"/);
  assert.match(research, /className="research-actions"/);
  assert.match(research, /className="metric-grid research-grid"/);
  assert.doesNotMatch(research, /minmax\(400px/);
  assert.match(narratives, /className="narrative-extraction-layout"/);
  assert.match(narratives, /htmlFor=\{`narrative-claim-\$\{cluster\.id\}`\}/);
  assert.match(styles, /\.brief-comparison-grid/);
  assert.match(styles, /\.research-grid/);
  assert.match(styles, /\.narrative-extraction-layout/);
});

test("daily brief keeps portfolio moves nullable and every important claim source-linked", () => {
  const page = readFrontendFile("app/daily-brief/page.tsx");
  const card = readFrontendFile("components/briefing-event-card.tsx");
  const api = readFrontendFile("lib/api/daily-brief.ts");
  const actions = readFrontendFile("app/actions.ts");
  const styles = readFrontendFile("app/globals.css");
  const smoke = readFrontendFile("e2e/daily-brief-runtime-smoke.spec.ts");
  const packageJson = readFrontendFile("package.json");

  assert.match(page, /move\.move_percent == null/);
  assert.match(page, /Move unavailable/);
  assert.match(page, /valuation_analysis_status === "not_run"/);
  assert.match(page, /AI Interpretation until reviewed/);
  assert.match(page, /source_market_price_ids\.length/);
  assert.match(page, /title="Inspection Queue"/);
  assert.match(page, /action\.source_event_ids\.map/);
  assert.match(page, /action\.source_raw_document_ids\.map/);
  assert.match(page, /title="Processing Failures"/);
  assert.match(page, /brief\.reviewed_at/);
  assert.match(page, /serverFetchApiResponse<DailyBriefSchedule \| null>\("\/daily-brief-schedule"\)/);
  assert.match(page, /<DailyBriefScheduleForm schedule=\{scheduleRes\.data\}/);
  assert.match(page, /errors=\{briefRes\.errors\}/);
  assert.match(page, /errors=\{scheduleRes\.errors\}/);
  assert.match(page, /\/events\/\$\{move\.event_id\}\/evidence-resolution/);
  assert.match(card, /\/events\/\$\{event_id\}\/evidence-resolution/);
  assert.match(card, /\/documents\/\$\{raw_document_id\}\/sections/);
  assert.match(card, /Source linked/);
  assert.match(api, /move_percent: number \| null/);
  assert.match(api, /claim_type: "AI Interpretation"/);
  assert.match(api, /claim_type: "Calculation"/);
  assert.match(api, /processing_run_id: number/);
  assert.match(actions, /export async function generateDailyBrief/);
  assert.match(styles, /\.briefing-summary-grid/);
  assert.match(styles, /\.briefing-source-grid/);
  assert.match(smoke, /move\?\.move_percent/);
  assert.match(smoke, /source_market_price_ids/);
  assert.match(smoke, /evidence-resolution/);
  assert.match(packageJson, /test:e2e:brief/);
});

test("daily brief scheduling is local, bounded, audited, and explicit", () => {
  const form = readFrontendFile("components/daily-brief-schedule-form.tsx");
  const actions = readFrontendFile("app/actions.ts");
  const serverApi = readFrontendFile("lib/server-api.ts");
  const styles = readFrontendFile("app/globals.css");
  const compose = readRepositoryFile("docker-compose.yml");

  assert.match(form, /Enable local schedule/);
  assert.match(form, /Rule-based, no external AI/);
  assert.match(form, /name="days_of_week"/);
  assert.match(form, /schedule\?\.due_now \? "Run due brief now" : "No brief is due"/);
  assert.match(actions, /serverPutApi<DailyBriefSchedule>\("\/daily-brief-schedule"/);
  assert.match(actions, /serverPostApi<DailyBriefScheduleRunResult>\("\/daily-brief-schedule\/run-due"/);
  assert.match(serverApi, /serverRequest<T>\("PUT", path, payload\)/);
  assert.match(styles, /\.briefing-schedule-layout/);
  assert.match(compose, /profiles: \["automation"\]/);
  assert.match(compose, /mem_limit: 256m/);
  assert.match(compose, /app\.workers\.daily_brief_scheduler/);
});

test("CSV import controls have unique programmatic labels", () => {
  const importer = readFrontendFile("components/csv-importer.tsx");
  const uploader = readFrontendFile("components/csv-upload-form.tsx");
  assert.match(importer, /const fileInputId = useId\(\)/);
  assert.match(importer, /<label htmlFor=\{fileInputId\}>CSV File<\/label>/);
  assert.match(importer, /id=\{fileInputId\}/);
  assert.match(uploader, /const fileInputId = useId\(\)/);
  assert.match(uploader, /htmlFor=\{fileInputId\}/);
  assert.match(uploader, /id=\{fileInputId\}/);
});

test("data management loads in parallel with valid responsive actions", () => {
  const dataPage = readFrontendFile("app/data/page.tsx");
  const styles = readFrontendFile("app/globals.css");

  assert.match(
    dataPage,
    /const \[companiesRes, sourcesRes, usCapabilitiesRes, indiaCapabilitiesRes\] = await Promise\.all/
  );
  assert.match(dataPage, /className="metric-grid data-management-grid"/);
  assert.doesNotMatch(dataPage, /<Link[^>]*>[\s\n]*<button/);
  assert.match(dataPage, /className="secondary-button" href="\/sources"/);
  assert.match(styles, /\.data-management-grid/);
});

test("system routes use labelled controls and bounded parallel setup", () => {
  const admin = readFrontendFile("app/admin/damodaran/page.tsx");
  const settings = readFrontendFile("app/settings/page.tsx");
  const search = readFrontendFile("app/search/page.tsx");
  const styles = readFrontendFile("app/globals.css");

  assert.match(admin, /htmlFor="damodaran-dataset-code"/);
  assert.match(admin, /id="damodaran-workbook"/);
  assert.doesNotMatch(admin, /catch \(err: any\)/);
  assert.match(settings, /const \[configRes, oauthStatusResult\] = await Promise\.all/);
  assert.match(search, /className="search-form"/);
  assert.match(styles, /\.search-form/);
});

test("portfolio attribution exposes partial calculations without fake FX or benchmarks", () => {
  const detail = readFrontendFile("components/portfolio/activity.tsx");
  const dashboard = readFrontendFile("components/portfolio-analytics.tsx");
  const api = readFrontendFile("lib/api/portfolio.ts");

  assert.match(detail, /Recorded Activity & Unrealized Change/);
  assert.match(detail, /Transaction activity remains separated by currency/);
  assert.match(detail, /Requires a selected benchmark series/);
  assert.match(detail, /Requires historical FX rates/);
  assert.match(detail, /attribution\.activity_by_currency/);
  assert.match(dashboard, /Not Configured/);
  assert.match(api, /calculation_status: "partial" \| "not_available"/);
  assert.match(api, /activity_by_currency: Record<string, PortfolioTransactionActivity>/);
  assert.doesNotMatch(detail, /Performance Attribution/);
});

test("portfolio performance uses owned setup, generated snapshots, and dated calculations", () => {
  const detail = readFrontendFile("components/portfolio/setup.tsx") + readFrontendFile("components/portfolio/performance-view.tsx");
  const setup = readFrontendFile("components/portfolio-performance-setup.tsx");
  const panel = readFrontendFile("components/portfolio-performance-panel.tsx");
  const actions = readFrontendFile("app/actions.ts");
  const api = readFrontendFile("lib/api/portfolio.ts");

  assert.match(detail, /PortfolioPerformanceSetup/);
  assert.match(detail, /PortfolioPerformancePanel/);
  assert.match(detail, /\/performance\?start_date=/);
  assert.match(detail, /\/period-attribution\?start_date=/);
  assert.match(detail, /\/opportunity-cost\?start_date=/);
  assert.match(detail, /capturePortfolioSnapshot/);
  assert.doesNotMatch(detail, /createPortfolioSnapshot|updatePortfolioSnapshot/);

  assert.match(setup, /Period returns require complete dated snapshots/);
  assert.match(setup, /createPortfolioBenchmark/);
  assert.match(setup, /createFxRateObservation/);
  assert.match(setup, /Remove Benchmark/);
  assert.match(setup, /Historical FX/);

  assert.match(panel, /attribution\.blockers/);
  assert.match(panel, /formula/);
  assert.match(panel, /source_snapshot_ids/);
  assert.match(panel, /Reconciliation Residual/);
  assert.match(panel, /Opportunity Cost/);
  assert.doesNotMatch(panel, /mock|placeholder/i);

  assert.match(actions, /portfolios\/\$\{portfolioId\}\/snapshots\/capture/);
  assert.match(actions, /portfolio-benchmarks/);
  assert.match(actions, /fx-rates/);
  assert.match(api, /export type PortfolioPerformance/);
  assert.match(api, /export type PortfolioPeriodAttribution/);
  assert.match(api, /export type PortfolioOpportunityCost/);
});

test("portfolio risk comparison labels calculations and estimates without requiring setup clicks", () => {
  const detail = readFrontendFile("components/portfolio/performance-view.tsx");
  const panel = readFrontendFile("components/portfolio-risk-return-panel.tsx");
  const api = readFrontendFile("lib/api/portfolio.ts");

  assert.match(detail, /PortfolioRiskReturnPanel/);
  assert.match(detail, /risk-return-comparison\?as_of_date=/);
  assert.match(panel, /Annualized volatility/);
  assert.match(panel, /Risk from \+1% weight/);
  assert.match(panel, /DCF valuation gap/);
  assert.match(panel, /This is not an annualized forecast/);
  assert.match(panel, /source_market_price_ids/);
  assert.match(panel, /source_fx_observation_ids/);
  assert.match(panel, /source_dcf_output_ids/);
  assert.match(panel, /comparison\.contains_mock_data/);
  assert.match(panel, /MockDataBadge/);
  assert.match(api, /export type PortfolioRiskReturn/);
  assert.match(api, /expected_return_claim_type: "Estimate" \| "Unavailable"/);
});

test("portfolio detail exposes an honest real-input readiness audit", () => {
  const detail = readFrontendFile("components/portfolio/setup.tsx");
  const panel = readFrontendFile("components/portfolio-real-input-readiness-panel.tsx");
  const api = readFrontendFile("lib/api/portfolio.ts");

  assert.match(detail, /PortfolioRealInputReadinessPanel/);
  assert.match(detail, /\/portfolios\/\$\{portfolioId\}\/real-input-readiness/);
  assert.match(detail, /serverFetchApiResponse<PortfolioRealInputReadiness>/);
  assert.match(panel, /DataStateNotices/);
  assert.match(panel, /Ready for the manual real-input smoke/);
  assert.match(panel, /Readiness verifies persisted evidence, not an investment conclusion/);
  assert.match(panel, /Mock Data was detected/);
  assert.match(panel, /Next: \{check\.message\}/);
  assert.match(panel, /Market price IDs/);
  assert.match(panel, /FX observation IDs/);
  assert.match(panel, /DCF output IDs/);
  assert.match(api, /export type PortfolioRealInputReadiness/);
  assert.match(api, /certification_status: "ready" \| "blocked"/);
});

test("portfolio evidence import requires server preview, provenance, and exact-file apply", () => {
  const detail = readFrontendFile("components/portfolio/setup.tsx");
  const importer = readFrontendFile("components/portfolio/portfolio-evidence-importer.tsx");

  assert.match(detail, /PortfolioEvidenceImporter/);
  assert.match(importer, /evidence-bundle\/template/);
  assert.match(importer, /evidence-bundle\/preview/);
  assert.match(importer, /evidence-bundle\/apply/);
  assert.match(importer, /expected_sha256/);
  assert.match(importer, /preview\.can_apply/);
  assert.match(importer, /provider, source URL, and source timestamp/);
  assert.match(importer, /does not independently verify the provider/);
  assert.doesNotMatch(importer, /Successfully imported \$\{preview\.total_rows\}/);
});

test("portfolio runtime smoke covers multi-currency risk, benchmark, snapshots, and DCF provenance", () => {
  const spec = readFrontendFile("e2e/portfolio-runtime-smoke.spec.ts");
  const seed = readRepositoryFile("scripts/seed_e2e_reference_data.py");
  const packageJson = readFrontendFile("package.json");

  assert.match(spec, /risk-return-comparison\?as_of_date=/);
  assert.match(spec, /period-attribution\?start_date=/);
  assert.match(spec, /opportunity-cost\?start_date=/);
  assert.match(spec, /source_fx_observation_ids/);
  assert.match(spec, /source_dcf_output_ids/);
  assert.match(spec, /contains_mock_data/);
  assert.match(spec, /not an annualized forecast/i);
  assert.match(seed, /Mock Data Multi-Currency Portfolio/);
  assert.match(seed, /range\(22\)/);
  assert.match(seed, /PortfolioBenchmarkConfig/);
  assert.match(seed, /PortfolioSnapshot/);
  assert.match(seed, /e2e_mock_fixture/);
  assert.match(readFrontendFile("components/portfolio-risk-return-panel.tsx"), /MockDataBadge/);
  assert.match(packageJson, /test:e2e:portfolio/);
  assert.doesNotMatch(readFrontendFile("components/portfolio-risk-return-panel.tsx"), /fontSize: "0\.72rem"/);
});

test("portfolio overview hides DCF outputs that fail trust gates", () => {
  const page = readFrontendFile("app/portfolio/page.tsx");
  const api = readFrontendFile("lib/api/portfolio.ts");

  assert.match(page, /href=\{`\/portfolio\/\$\{portfolio\.id\}`\}/);
  assert.doesNotMatch(page, /\/analytics|\/portfolio-snapshots/);
  assert.match(page, /valuation_status === "trusted"/);
  assert.match(page, />Untrusted</);
  assert.match(page, />Unavailable</);
  assert.match(api, /valuation_status\?: "trusted" \| "stale" \| "untrusted" \| "unavailable"/);
});

test("market regime exposes bounded inputs and calculation provenance", () => {
  const page = readFrontendFile("app/portfolio/regime/page.tsx");
  const form = readFrontendFile("components/portfolio/RegimeInputForm.tsx");
  const fredPanel = readFrontendFile("components/portfolio/fred-macro-regime-panel.tsx");
  const actions = readFrontendFile("app/actions.ts");
  const api = readFrontendFile("lib/api/market.ts");

  assert.match(page, /score\.calculation_status === "blocked"/);
  assert.match(page, /Provider-backed modules/);
  assert.match(page, /score\.manual_modules/);
  assert.match(page, /Input Evidence & Freshness/);
  assert.match(page, /score\.input_sources/);
  assert.match(page, /source\.claim_type/);
  assert.match(page, /source\.source_record_id/);
  assert.match(page, /score\.formula/);
  assert.match(page, /score\.blockers/);
  assert.doesNotMatch(page, /PrototypeBadge/);
  assert.match(form, /Normalized Score \(-100 to 100\)/);
  assert.match(form, /min="-100"/);
  assert.match(form, /max="100"/);
  assert.match(form, /Provider-backed observation/);
  assert.match(form, /Normalization Methodology/);
  assert.match(form, /required=\{inputType === "provider"\}/);
  for (const id of ["metric-name", "normalized-score", "input-type", "source-name", "source-url", "methodology", "as-of-date"]) {
    assert.match(form, new RegExp(`htmlFor="${id}"`));
    assert.match(form, new RegExp(`id="${id}"`));
  }
  assert.match(page, /className="regime-layout"/);
  assert.match(page, /FredMacroRegimePanel/);
  assert.match(page, /market-regime\/providers\/fred\/macro\/preview/);
  assert.doesNotMatch(page, /source\.input_type === "manual" \? "User Assumption" : "Fact"/);
  assert.match(fredPanel, /National Financial Conditions Index/);
  assert.match(fredPanel, /Provider values are transformed by the disclosed formula/);
  assert.match(fredPanel, /Macro series record/);
  assert.match(fredPanel, /Observation record/);
  assert.match(fredPanel, /does not fetch data, trade, or produce investment advice/);
  assert.match(actions, /applyFredMacroRegimeInputWithState/);
  assert.match(actions, /market-regime\/providers\/fred\/macro\/apply/);
  assert.match(api, /calculation_status: "complete" \| "stale" \| "blocked"/);
  assert.match(api, /input_type: "manual" \| "provider"/);
  assert.match(api, /export type MarketRegimeMacroProviderRead/);
  assert.match(api, /claim_type: "Calculation" \| "Source Summary" \| "User Assumption"/);
});

test("macro series UI exposes provider provenance and observation record IDs", () => {
  const page = readFrontendFile("app/macro/page.tsx");
  const api = readFrontendFile("lib/api/macro.ts");

  assert.match(page, /Source: \{series\.provider_name \|\| "Manual"\}/);
  assert.match(page, /Open provider series/);
  assert.match(page, /#\{obs\.id\}/);
  assert.match(api, /provider_name: string \| null/);
  assert.match(api, /source_url: string \| null/);
});

test("AI research uses the same complete citation and human-review workflow", () => {
  const controls = readFrontendFile("components/ai-output-review-controls.tsx");
  const metadata = readFrontendFile("components/ai-metadata.tsx");
  const session = readFrontendFile("app/research/sessions/[id]/page.tsx");
  const api = readFrontendFile("lib/api/ai.ts");

  assert.match(controls, /output_text\.matchAll/);
  assert.match(controls, /Validate all cited sources/);
  assert.match(controls, /citedSourceIds\.map/);
  assert.match(controls, /Find exact passage candidates/);
  assert.match(controls, /deterministic lexical matches from stored text/);
  assert.match(controls, /applyCitationCandidate/);
  assert.match(controls, /Selecting one does not[\s\S]*validate the claim or approve this output/);
  assert.match(controls, /!output\.evaluation_json\?\.passed/);
  assert.match(controls, /citation_source_coverage|Object\.entries\(output\.evaluation_json\.checks\)/);
  assert.match(session, /AiOutputReviewControls initialOutput=\{msg\.ai_output\}/);
  assert.match(metadata, /Human review:/);
  assert.match(metadata, /cit\.reason/);
  assert.match(api, /is_blocked: boolean/);
  assert.match(api, /AiCitationSuggestionCandidate/);
  assert.match(api, /citations\/suggestions/);
});

test("data health exposes the authenticated evidence integrity report", () => {
  const page = readFrontendFile("app/data-health/page.tsx") + readFrontendFile("components/peer-receipt-health-panel.tsx");
  const runtimePanel = readFrontendFile("components/runtime-readiness-panel.tsx");
  const api = readFrontendFile("lib/api/health.ts");
  const styles = readFrontendFile("app/globals.css");
  assert.match(page, /\/data-health\/evidence-integrity\?deep=true/);
  assert.match(page, /Fast health check/);
  assert.match(page, /Run deep evidence audit/);
  assert.match(page, /timeoutMs: 60_000/);
  assert.match(page, /evidenceIntegrityRes\?\.data/);
  assert.match(page, /evidenceIntegrityRes\.errors/);
  assert.match(page, /Evidence Integrity/);
  assert.match(page, /Required Action/);
  assert.match(page, /issue\.document_id/);
  assert.match(page, /Financial certification/);
  assert.match(page, /label="Financial facts"/);
  assert.match(page, /Financial History Certification/);
  assert.match(page, /statement_identity_status/);
  assert.match(page, /className="health-command-bar"/);
  assert.match(page, /aria-labelledby="operations-health-title"/);
  assert.match(page, /aria-labelledby="provider-readiness-title"/);
  assert.match(page, /aria-labelledby="diagnostic-status-title"/);
  assert.match(page, /evidenceIntegrity \? evidenceIntegrity\.error_count : "Not run"/);
  assert.match(page, /evidenceIntegrity \? evidenceIntegrity\.certified_markets\.join\(", "\) \|\| "None" : "Not run"/);
  assert.doesNotMatch(page, /className="metric-grid" style=\{\{ marginBottom: "2rem" \}\}/);
  assert.match(styles, /\.health-metric-grid/);
  assert.match(styles, /\.health-diagnostic-grid/);
  assert.match(page, /serverFetchApiResponse<RuntimeReadiness>\("\/api\/readiness"\)/);
  assert.match(page, /<RuntimeReadinessPanel/);
  assert.match(page, /\/data-health\/peer-review-receipts/);
  assert.match(page, /Peer Review Receipts/);
  assert.match(page, /sets_requiring_attention/);
  assert.match(page, /missing_receipt_count/);
  assert.match(page, /stale_receipt_count/);
  assert.match(page, /\/companies\/\$\{item\.company_id\}\/valuation\/peers#peer-set-/);
  assert.match(page, /Counts below apply only to this page/);
  assert.match(page, /total_owned_set_count/);
  assert.match(page, /storage_blocked_count/);
  assert.match(page, /next_after_id/);
  assert.match(api, /export type PeerReviewReceiptHealth/);
  assert.match(runtimePanel, /Liveness only proves that a process exists/);
  assert.match(runtimePanel, /expected_migration_head/);
  assert.match(runtimePanel, /missing_tables/);
  assert.match(runtimePanel, /docker compose exec backend alembic upgrade head/);
});

test("stale and unavailable notices describe distinct data states", () => {
  const states = readFrontendFile("components/ui/data-states.tsx");
  assert.match(states, /Stored source data is older than its freshness threshold/);
  assert.match(states, /Data unavailable:/);
  assert.match(states, /No cached replacement is being shown/);
  assert.match(states, /missing panels are not cache fallbacks/);
  assert.doesNotMatch(states, /backend is currently unreachable/);
  assert.doesNotMatch(states, /showing cached data/i);
  assert.doesNotMatch(states, /fontSize: "0\.7rem"/);
});

test("navigation and AI provenance labels avoid sub-12px text", () => {
  const styles = readFrontendFile("app/globals.css");
  const aiMetadata = readFrontendFile("components/ai-metadata.tsx");

  assert.match(
    styles,
    /\.nav-group-label\s*\{[\s\S]*?font-size:\s*var\(--font-size-xs\)/,
  );
  assert.doesNotMatch(aiMetadata, /fontSize:\s*["']0\.7rem["']/);
});

test("provider health exposes run classification, freshness, and owned coverage", () => {
  const page = readFrontendFile("app/data-health/page.tsx");
  const api = readFrontendFile("lib/api/operations.ts");

  assert.match(page, /Latest Attempt/);
  assert.match(page, /provider\.latest_run_status/);
  assert.match(page, /provider\.recent_run_count/);
  assert.match(page, /provider\.consecutive_failures/);
  assert.match(page, /provider\.freshness_label/);
  assert.match(page, /provider\.coverage_state/);
  assert.match(page, /provider\.requirement_level/);
  assert.match(page, /label="Required config gaps"/);
  assert.match(page, /label="Optional integrations"/);
  assert.match(api, /last_attempt_at: string \| null/);
  assert.match(api, /requirement_level: "core" \| "optional" \| "manual"/);
  assert.match(api, /data_age_hours: number \| null/);
  assert.match(api, /configured_source_count: number \| null/);
  assert.match(api, /\| "running"/);
  assert.match(api, /\| "partial"/);
});


test("data health exposes deterministic historical event evidence backfill", () => {
  const page = readFrontendFile("app/data-health/page.tsx");
  const actions = readFrontendFile("app/actions.ts");
  const api = readFrontendFile("lib/api/health.ts");

  assert.match(page, /Historical Event Evidence Backfill/);
  assert.match(page, /event-evidence-backfill\?limit=100/);
  assert.match(page, /Fuzzy matching is disabled/);
  assert.match(page, /applyEventEvidenceBackfill/);
  assert.match(actions, /dry_run: false/);
  assert.match(actions, /event-evidence-backfill/);
  assert.match(api, /EventEvidenceBackfillReport/);
});


test("data health exposes typed Damodaran application coverage", () => {
  const page = readFrontendFile("app/data-health/page.tsx");
  const api = readFrontendFile("lib/api/health.ts");

  assert.match(page, /serverFetchApiResponse<DamodaranCoverageReport>\("\/data-health\/damodaran-coverage"/);
  assert.match(page, /Damodaran Application Coverage/);
  assert.match(page, /coverage\.implementation_status/);
  assert.match(page, /coverage\.ingestion_status/);
  assert.match(page, /coverage\.typed_record_count/);
  assert.match(page, /coverage\.provenance_status/);
  assert.match(page, /coverage\.active_source_sha256/);
  assert.match(page, /coverage\.freshness_status/);
  assert.match(page, /coverage\.missing_metrics/);
  assert.match(page, /coverage\.action_required/);
  assert.match(api, /export type DamodaranCoverageReport/);
  assert.match(api, /"metadata_only" \| "not_ingested" \| "source_missing"/);
  assert.match(api, /"user_assumed_recent"/);
});


test("fundamentals exposes financial statement identity checks", () => {
  const page = readFrontendFile("app/companies/[id]/fundamentals/page.tsx");
  const api = readFrontendFile("lib/api/financials.ts");

  assert.match(page, /Statement Identities/);
  assert.match(page, /financial-statements\/identities/);
  assert.match(page, /check\.formula/);
  assert.match(page, /check\.missing_metrics/);
  assert.match(api, /FinancialStatementIdentityReport/);
  assert.match(api, /getFinancialStatementIdentities/);
});


test("financial candidates expose bounded rendered PDF evidence overlays", () => {
  const viewer = readFrontendFile("app/documents/[id]/financial-evidence/page.tsx");
  const helper = readFrontendFile("lib/financial-evidence.ts");
  const review = readFrontendFile("components/financial-candidate-review.tsx");

  assert.match(viewer, /asset\/pages\/\$\{geometry\.pageNumber\}\.png\?scale=1\.5/);
  assert.match(viewer, /financial-evidence-box/);
  assert.match(viewer, /Open source PDF/);
  assert.match(viewer, /Document-level fallback/);
  assert.match(helper, /pdfplumber_top_left_points/);
  assert.match(helper, /x1 > pageWidth \|\| bottom > pageHeight/);
  assert.match(helper, /pdf_reported_component_sum|componentRecords/);
  assert.match(review, /financialEvidenceHref\(candidate\)/);
});


test("event PDF regions share the bounded renderer and preserve explicit fallbacks", () => {
  const viewer = readFrontendFile("app/documents/[id]/event-evidence/page.tsx");
  const helper = readFrontendFile("lib/financial-evidence.ts");
  const sections = readFrontendFile("app/documents/[id]/sections/page.tsx");
  const drawer = readFrontendFile("components/intelligence/EvidenceTrailDrawer.tsx");

  assert.match(viewer, /asset\/pages\/\$\{geometry\.pageNumber\}\.png\?scale=1\.5/);
  assert.match(viewer, /Exact PDF region/);
  assert.match(viewer, /Page-level fallback/);
  assert.match(helper, /eventEvidenceGeometry/);
  assert.match(helper, /pdf_region_status !== "valid"/);
  assert.match(helper, /event-evidence\?evidence_reference=/);
  assert.match(sections, /Open rendered region/);
  assert.match(drawer, /precision === "region"/);
});


test("stored corpus search exposes owned research filters and provenance", () => {
  const page = readFrontendFile("app/search/page.tsx");
  const api = readFrontendFile("lib/api/evidence.ts");

  assert.match(page, /serverFetchApiResponse<EvidenceSearchResult\[]>/);
  assert.match(page, /name="type"/);
  for (const label of [
    "Documents",
    "Events",
    "Alerts",
    "Thesis notes",
    "Decision journal",
    "Valuation models",
    "Narratives",
    "Research sessions",
    "Research messages",
    "Reviewed AI outputs",
  ]) {
    assert.match(page, new RegExp(label));
  }
  assert.match(page, /result\.claim_type/);
  assert.match(page, /result\.scope === "private"/);
  assert.match(page, /result\.review_status === "approved"/);
  assert.match(page, /result\.is_mock/);
  assert.match(page, /result\.source_timestamp/);
  for (const resultType of ["narrative", "research_session", "research_message", "ai_output"]) {
    assert.match(api, new RegExp(`\\| "${resultType}"`));
  }
  assert.match(api, /scope: "shared" \| "private"/);
  assert.match(api, /review_status: "not_applicable" \| "approved"/);
  assert.match(page, /Stored research search is unavailable/);
});


test("valuation industry mapping supports persisted revenue-weighted segments", () => {
  const card = readFrontendFile("components/valuation/industry-mapping-card.tsx");
  const api = readFrontendFile("lib/api/companies.ts");

  assert.match(card, /Revenue-Weighted Industry Mix/);
  assert.match(card, /Math\.abs\(totalWeight - 100\) <= 0\.01/);
  assert.match(card, /Save mix/);
  assert.match(card, /Saved as User Assumption/);
  assert.match(card, /benchmarkAvailability/);
  assert.match(card, /industry-mix-editor/);
  assert.doesNotMatch(card, /min-w-\[800px\]/);
  assert.match(card, /source_document_id/);
  assert.match(api, /fetchIndustryMix/);
  assert.match(api, /saveIndustryMix/);
  assert.match(api, /industry-allocations/);
});

test("valuation model deletion reports failures instead of silently submitting", () => {
  const page = readFrontendFile("app/companies/[id]/valuation/page.tsx");
  const actions = readFrontendFile("app/actions.ts");

  assert.match(page, /DeleteRecordForm/);
  assert.match(page, /deleteValuationModelWithState\.bind/);
  assert.match(actions, /export async function deleteValuationModelWithState/);
  assert.match(actions, /return formActionError\(error\)/);
});

test("valuation drafts allow one explicit confirmation for valid current defaults", () => {
  const review = readFrontendFile("components/valuation/autofill-draft-review.tsx");

  assert.match(review, /Use all current defaults/);
  assert.match(review, /acceptCurrentDefaults/);
  assert.match(review, /I understand these values are estimates/);
  assert.match(review, /valuation-draft-group/);
  assert.match(review, /valuation-draft-warnings/);
});

test("advanced valuation workspace is responsive and blocks misleading outputs", () => {
  const workspace = readFrontendFile("components/advanced-workspace.tsx");
  const sensitivity = readFrontendFile("components/valuation/sensitivity-tables-panel.tsx");
  const styles = readFrontendFile("app/globals.css");

  assert.match(workspace, /valuation-workspace-grid/);
  assert.match(workspace, /outputTrustBlocked/);
  assert.match(workspace, /Sensitivity tables are unavailable for this model/);
  assert.match(workspace, /invalidAssumptions\.length > 0/);
  assert.match(workspace, /<SavedValuationOutputCard state=\{outputState\}/);
  assert.match(workspace, /valuation-section-groups/);
  assert.match(sensitivity, /currency/);
  assert.doesNotMatch(sensitivity, /formatCurrency\(val, "INR"/);
  assert.match(styles, /\.valuation-workspace-grid/);
  assert.match(styles, /\.topbar \{[\s\S]*?background: var\(--color-surface\)/);
});

test("valuation pages expose load and action failures instead of swallowing them", () => {
  const modelsPage = readFrontendFile("app/companies/[id]/valuation/page.tsx");
  const detailPage = readFrontendFile("app/companies/[id]/valuation/[model_id]/page.tsx");
  const workspace = readFrontendFile("components/advanced-workspace.tsx");

  assert.doesNotMatch(modelsPage, /Ignored if missing/);
  assert.match(modelsPage, /Market context unavailable/);
  assert.match(modelsPage, /Model readiness/);
  assert.doesNotMatch(detailPage, /models\.find/);
  assert.match(detailPage, /\/valuation-models\/\$\{modelId\}/);
  assert.match(detailPage, /Market context unavailable/);
  assert.match(workspace, /saveError/);
  assert.match(workspace, /saveSuccess/);
  const reverse = readFrontendFile("components/valuation/reverse-dcf-panel.tsx");
  assert.match(workspace, /ReverseDcfPanel/);
  assert.match(reverse, /setError/);
  assert.match(reverse, /error && <p role="alert"/);
});

test("relative valuation requires reviewed source-labeled peer sets", () => {
  const panel = readFrontendFile("components/valuation/relative-valuation-panel.tsx");
  const manager = readFrontendFile("components/valuation/peer-set-manager.tsx");
  const api = readFrontendFile("lib/api/relative-valuation.ts");

  assert.match(panel, /Source-backed industry aggregate/);
  assert.match(panel, /User-reviewed peer set/);
  assert.match(panel, /peerSetId/);
  assert.match(panel, /isPeerSetCalculationReady/);
  assert.match(readFrontendFile("lib/relative-valuation-selection.ts"), /reviewReceipt\?\.matchesCurrentDiagnostics/);
  assert.match(panel, /current diagnostic receipt/);
  assert.match(panel, /memberSources/);
  assert.match(panel, /claimType/);
  assert.match(manager, /Every mutation is version-checked and retained in history/);
  assert.match(manager, /Restored or edited sets return to Draft/);
  assert.match(manager, /Source URL/);
  assert.match(manager, /Source as of/);
  assert.match(manager, /Review and approve/);
  assert.match(manager, /I reviewed the current diagnostic warning categories/);
  assert.match(manager, /Re-acknowledge current diagnostics/);
  assert.match(manager, /Diagnostic receipt/);
  assert.match(manager, /Existing evidence and revision history were retained/);
  assert.match(manager, /Save changes as new version/);
  assert.match(manager, /Restore as draft/);
  assert.match(manager, /comparability warning/);
  assert.match(manager, /Preview never writes/);
  assert.match(manager, /exact SHA-256 previewed file/);
  assert.match(manager, /creates a Draft/);
  assert.match(manager, /no duplicate was created/);
  assert.match(manager, /Retrying the exact file is safe/);
  assert.match(manager, /Imported facts are[\s\S]*user-supplied and are not independently verified/);
  assert.match(manager, /Storage audit/);
  assert.match(manager, /Export CSV/);
  assert.match(manager, /Fiscal period end/);
  assert.match(manager, /Accounting standard/);
  assert.match(manager, /Revenue growth %/);
  assert.match(manager, /EBITDA margin %/);
  assert.match(manager, /Sourced target-company comparability profile/);
  assert.match(manager, /Compare peers against sourced target facts/);
  assert.match(manager, /peer market caps grouped by stated currency/);
  assert.match(manager, /No FX conversion is applied/);
  assert.match(manager, /Target storage audit/);
  assert.match(manager, /Template v2 carries one identical sourced target-company profile/);
  assert.match(manager, /Legacy member-only files remain accepted with a visible warning/);
  assert.match(manager, /target profile[\s\S]*included[\s\S]*missing/);
  assert.match(manager, /readPeerCsvFile/);
  assert.match(manager, /csvSelection\.current/);
  assert.match(manager, /setCsvPreview\(null\)/);
  assert.match(manager, /busy \|\| csvLoading \|\| !csvPreview\?\.isValid/);
  assert.match(manager, /UTF-8 CSV only, up to 1 MB and 50 peer rows/);
  assert.match(api, /\/api\/valuation\/relative\/peer-sets/);
  assert.match(api, /targetContext/);
  assert.match(api, /targetStorageConsistency/);
  assert.match(api, /targetColumns/);
  assert.match(api, /legacyFormat/);
  assert.match(api, /targetContextIncluded/);
  assert.match(api, /marketCapGroups/);
  assert.match(api, /skippedCurrencyMismatchCount/);
  assert.match(api, /reviewPeerValuationSet/);
  assert.match(api, /expectedDiagnosticsSha256/);
  assert.match(api, /acknowledgedWarningCodes/);
  assert.match(api, /matchesCurrentDiagnostics/);
  assert.match(api, /archivePeerValuationSet/);
  assert.match(api, /restorePeerValuationSet/);
  assert.match(api, /listPeerValuationSetRevisions/);
  assert.match(api, /getPeerCsvTemplate/);
  assert.match(api, /previewPeerCsv/);
  assert.match(api, /applyPeerCsv/);
  assert.match(api, /PeerCsvApplyResult/);
  assert.match(api, /importDisposition: "created" \| "reused"/);
  assert.match(api, /exportPeerValuationSet/);
});


test("quick valuation uses typed non-persisting backend calculations", () => {
  const workflow = readFrontendFile("components/quick-valuation-workflow.tsx");
  const api = readFrontendFile("lib/api/valuation.ts");

  assert.match(workflow, /\/api\/valuation\/quick\/assumptions/);
  assert.match(workflow, /\/api\/valuation\/quick\/calculate/);
  assert.doesNotMatch(workflow, /\/valuation\/assumptions\/generate/);
  assert.doesNotMatch(workflow, /\/valuation\/dcf\/calculate/);
  assert.doesNotMatch(workflow, /falling back to empty fields/i);
  assert.match(workflow, /quick result is not saved/i);
  assert.match(workflow, /valuationOutput\.claim_type/);
  assert.match(api, /export type QuickValuationAssumptions/);
  assert.match(api, /export type QuickValuationOutput/);
});


test("historical events expose bounded exact-span evidence resolution", () => {
  const page = readFrontendFile("app/events/[id]/evidence-resolution/page.tsx");
  const form = readFrontendFile("components/event-evidence-resolution-form.tsx");
  const actions = readFrontendFile("app/actions.ts");
  const dataHealth = readFrontendFile("app/data-health/page.tsx");
  const api = readFrontendFile("lib/api/evidence.ts");

  assert.match(page, /evidence-resolution\/search/);
  assert.match(page, /context_chars: "180"/);
  assert.match(page, /limit: "25"/);
  assert.match(page, /match\.context_before/);
  assert.match(page, /<mark>\{match\.quote\}<\/mark>/);
  assert.match(page, /Full source text is not returned/);
  assert.match(form, /document_content_hash/);
  assert.match(form, /occurrence_index/);
  assert.match(actions, /manual|evidence-resolution/);
  assert.match(actions, /revalidatePath\("\/data-health"\)/);
  assert.match(dataHealth, /Resolve exact span/);
  assert.match(api, /export type EventEvidenceResolutionSearch/);
});
