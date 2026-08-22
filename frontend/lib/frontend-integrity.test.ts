import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import test from "node:test";

const frontendRoot = fileURLToPath(new URL("../", import.meta.url));

function readFrontendFile(filePath: string): string {
  return readFileSync(path.join(frontendRoot, filePath), "utf8");
}

function readRepositoryFile(filePath: string): string {
  return readFileSync(path.join(frontendRoot, "..", filePath), "utf8");
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


test("Docker development keeps Linux native modules outside the host bind mount", () => {
  const compose = readRepositoryFile("docker-compose.yml");

  assert.match(compose, /npm ci --prefer-offline --no-audit/);
  assert.match(compose, /- \/app\/node_modules/);
  assert.match(compose, /- \/app\/\.next/);
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
  assert.doesNotMatch(timeline, /fontSize: "0\.7rem"/);
  assert.doesNotMatch(workspace, /fontSize: "0\.7rem"/);
  assert.doesNotMatch(diagnostics, /fontSize: "0\.7rem"/);
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
  assert.match(dashboard, /overviewWarnings\.join/);
  assert.match(dashboard, /defaultPortfolioSnapshot\.snapshot_date/);
  assert.match(dashboard, /defaultPortfolio \? "Add Prices" : "\+ Connect Portfolio"/);
});

test("research routes use parallel requests and responsive layouts", () => {
  const brief = readFrontendFile("app/daily-brief/page.tsx");
  const research = readFrontendFile("app/research/page.tsx");
  const narratives = readFrontendFile("app/narratives/page.tsx");
  const styles = readFrontendFile("app/globals.css");

  assert.match(brief, /const \[briefRes, savedBriefsRes\] = await Promise\.all/);
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
  const detail = readFrontendFile("app/portfolio/[id]/page.tsx");
  const dashboard = readFrontendFile("components/portfolio-analytics.tsx");
  const api = readFrontendFile("lib/api.ts");

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
  const detail = readFrontendFile("app/portfolio/[id]/page.tsx");
  const setup = readFrontendFile("components/portfolio-performance-setup.tsx");
  const panel = readFrontendFile("components/portfolio-performance-panel.tsx");
  const actions = readFrontendFile("app/actions.ts");
  const api = readFrontendFile("lib/api.ts");

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
  const detail = readFrontendFile("app/portfolio/[id]/page.tsx");
  const panel = readFrontendFile("components/portfolio-risk-return-panel.tsx");
  const api = readFrontendFile("lib/api.ts");

  assert.match(detail, /PortfolioRiskReturnPanel/);
  assert.match(detail, /risk-return-comparison\?as_of_date=/);
  assert.match(panel, /Annualized volatility/);
  assert.match(panel, /Risk from \+1% weight/);
  assert.match(panel, /DCF valuation gap/);
  assert.match(panel, /This is not an annualized forecast/);
  assert.match(panel, /source_market_price_ids/);
  assert.match(panel, /source_fx_observation_ids/);
  assert.match(panel, /source_dcf_output_ids/);
  assert.doesNotMatch(panel, /mock|placeholder/i);
  assert.match(api, /export type PortfolioRiskReturn/);
  assert.match(api, /expected_return_claim_type: "Estimate" \| "Unavailable"/);
});

test("portfolio overview hides DCF outputs that fail trust gates", () => {
  const page = readFrontendFile("app/portfolio/page.tsx");
  const api = readFrontendFile("lib/api.ts");

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
  const api = readFrontendFile("lib/api.ts");

  assert.match(page, /score\.calculation_status === "blocked"/);
  assert.match(page, /Provider-backed modules/);
  assert.match(page, /score\.manual_modules/);
  assert.match(page, /Input Evidence & Freshness/);
  assert.match(page, /score\.input_sources/);
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
  assert.match(api, /calculation_status: "complete" \| "stale" \| "blocked"/);
  assert.match(api, /input_type: "manual" \| "provider"/);
});

test("AI research uses the same complete citation and human-review workflow", () => {
  const controls = readFrontendFile("components/ai-output-review-controls.tsx");
  const metadata = readFrontendFile("components/ai-metadata.tsx");
  const session = readFrontendFile("app/research/sessions/[id]/page.tsx");
  const api = readFrontendFile("lib/api.ts");

  assert.match(controls, /output_text\.matchAll/);
  assert.match(controls, /Validate all cited sources/);
  assert.match(controls, /citedSourceIds\.map/);
  assert.match(controls, /!output\.evaluation_json\?\.passed/);
  assert.match(controls, /citation_source_coverage|Object\.entries\(output\.evaluation_json\.checks\)/);
  assert.match(session, /AiOutputReviewControls initialOutput=\{msg\.ai_output\}/);
  assert.match(metadata, /Human review:/);
  assert.match(metadata, /cit\.reason/);
  assert.match(api, /is_blocked: boolean/);
});

test("data health exposes the authenticated evidence integrity report", () => {
  const page = readFrontendFile("app/data-health/page.tsx");
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
});

test("stale notices do not claim cached data when a caller supplies a specific failure message", () => {
  const states = readFrontendFile("components/ui/data-states.tsx");
  assert.match(states, /message \|\| "The backend is currently unreachable\. Showing cached data\."/);
  assert.doesNotMatch(states, /lastUpdated \?[^\n]+: " \(The backend is currently unreachable\. Showing cached data\.\)"/);
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
  const api = readFrontendFile("lib/api.ts");

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
  const api = readFrontendFile("lib/api.ts");

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
  const api = readFrontendFile("lib/api.ts");

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
  const api = readFrontendFile("lib/api.ts");

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
  const api = readFrontendFile("lib/api.ts");

  assert.match(page, /serverFetchApiResponse<EvidenceSearchResult\[]>/);
  assert.match(page, /name="type"/);
  for (const label of ["Documents", "Events", "Alerts", "Thesis notes", "Decision journal", "Valuation models"]) {
    assert.match(page, new RegExp(label));
  }
  assert.match(page, /result\.claim_type/);
  assert.match(page, /result\.source_timestamp/);
  assert.match(api, /"document" \| "event" \| "alert" \| "thesis" \| "decision" \| "valuation"/);
});


test("valuation industry mapping supports persisted revenue-weighted segments", () => {
  const card = readFrontendFile("components/valuation/industry-mapping-card.tsx");
  const api = readFrontendFile("lib/api.ts");

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
  assert.match(workspace, /formatCurrency\(out\?\.intrinsic_value_per_share, outputCurrency\)/);
  assert.match(workspace, /valuation-section-groups/);
  assert.match(sensitivity, /currency/);
  assert.doesNotMatch(sensitivity, /formatCurrency\(val, "INR"/);
  assert.match(styles, /\.valuation-workspace-grid/);
  assert.match(styles, /\.topbar \{[\s\S]*?background: var\(--color-surface\)/);
});


test("quick valuation uses typed non-persisting backend calculations", () => {
  const workflow = readFrontendFile("components/quick-valuation-workflow.tsx");
  const api = readFrontendFile("lib/api.ts");

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
  const api = readFrontendFile("lib/api.ts");

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
