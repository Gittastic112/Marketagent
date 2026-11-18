import { RetainedActionForm } from "@/components/retained-action-form";
import { notFound } from "next/navigation";
import Link from "next/link";
import { RefreshCw } from "lucide-react";
import type {
  Company,
  FinancialExtractionCandidate,
  FinancialReconciliation,
  FinancialStatementIdentityReport,
  FinancialStatementPeriod,
  NormalizedCoverage,
  NormalizedSnapshotRead,
} from "@/lib/api";
import { serverFetchApi, serverFetchApiResponse } from "@/lib/server-api";
import { summarizeApiMetas, hasUsableData } from "@/lib/data-state-meta";
import { ApiError } from "@/lib/api/contract";
import { ErrorState } from "@/components/page";
import { DataHealthUpdater } from "@/components/providers/data-health-updater";
import { DataStateNotices } from "@/components/ui/data-states";
import { backfillNormalizedFinancialsAction, deleteFinancialStatementPeriod, normalizeFinancialPeriodAction } from "@/app/actions";
import { FinancialCandidateReview } from "@/components/financial-candidate-review";
import { FinancialReviewPlanPanel } from "@/components/financial-review-plan";
import { FinancialSourceHistory } from "@/components/financial-source-history";
import { DatedFinancialInputs } from "@/components/dated-financial-inputs";
import type { DatedInputs } from "@/lib/api/dated-inputs";
import type { FinancialReviewPlan, SourceFactRevision } from "@/lib/api/financials";
import { ScreenerUpload } from "@/components/screener-upload";
import { formatNumber } from "@/lib/formatting";
import { financialIdentityFormula, financialMetricLabel } from "@/lib/financial-evidence";

export default async function FundamentalsPage(props: { params: Promise<{ id: string }>; searchParams?: Promise<Record<string, string | string[] | undefined>> }) {
  const params = await props.params;
  const companyId = parseInt(params.id, 10);
  if (isNaN(companyId)) {
    notFound();
  }

  let company: Company;
  try {
    company = await serverFetchApi<Company>(`/companies/${companyId}`);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) notFound();
    return <ErrorState message="Company fundamentals could not be loaded. Reload to retry." />;
  }

  const query = (await props.searchParams) ?? {};
  const first = (value: string | string[] | undefined) => (Array.isArray(value) ? value[0] : value)?.trim() ?? "";
  const reviewTrack = first(query.review_track) || "operating";
  const reviewYear = first(query.review_year);
  const valuationDate = first(query.valuation_date) || new Date().toISOString().slice(0, 10);
  const knowledge = first(query.knowledge) || "available_by_date";
  const datedParams = new URLSearchParams({ valuation_date: valuationDate, knowledge, track: reviewTrack });
  const reviewParams = new URLSearchParams({track: reviewTrack});
  if (reviewYear) reviewParams.set("latest_year", reviewYear);
  const [periodsRes, extractedCandidatesRes, normalizedSnapshotsRes, coverageResponse, reconciliationResponse, identityResponse, reviewPlanResponse, sourceFactsResponse, datedResponse] = await Promise.all([
    serverFetchApiResponse<FinancialStatementPeriod[]>(`/companies/${companyId}/financial-periods`),
    serverFetchApiResponse<FinancialExtractionCandidate[]>(`/api/companies/${companyId}/financial-statements/extracted?include_promoted=true`),
    serverFetchApiResponse<NormalizedSnapshotRead[]>(`/api/companies/${companyId}/financial-statements/normalized`),
    serverFetchApiResponse<NormalizedCoverage>(`/api/companies/${companyId}/financial-statements/normalized/coverage`),
    serverFetchApiResponse<FinancialReconciliation>(
      `/api/companies/${companyId}/financial-statements/normalized/reconciliation`,
    ),
    serverFetchApiResponse<FinancialStatementIdentityReport>(
      `/api/companies/${companyId}/financial-statements/identities`,
    ),
    serverFetchApiResponse<FinancialReviewPlan>("/api/companies/" + companyId + "/financial-statements/review-plan?" + reviewParams),
    serverFetchApiResponse<SourceFactRevision[]>(`/companies/${companyId}/source-facts`),
    serverFetchApiResponse<DatedInputs>(`/companies/${companyId}/dated-inputs?${datedParams}`),
  ]);
  const periods = periodsRes.data || [];
  const evidenceCandidates = extractedCandidatesRes.data || [];
  const extractedCandidates = evidenceCandidates.filter(candidate => candidate.review_status !== "promoted");
  const normalizedSnapshots = normalizedSnapshotsRes.data || [];
  const coverage = coverageResponse.data;
  const reconciliation = reconciliationResponse.data;
  const identityReport = identityResponse.data;

  const dataState = summarizeApiMetas([
    periodsRes.meta,
    extractedCandidatesRes.meta,
    normalizedSnapshotsRes.meta,
    coverageResponse.meta,
    reconciliationResponse.meta,
    identityResponse.meta,
    sourceFactsResponse.meta,
  ]);
  const reconciliationIssues = reconciliation?.periods.flatMap((period) =>
    period.items
      .filter((item) => item.status !== "exact")
      .map((item) => ({ ...item, period })),
  ) || [];

  return (
    <div className="space-y-6">
      <DataHealthUpdater segment="fundamentals" isStale={dataState.someStale || dataState.allStale} />
      <DataStateNotices metas={[
        periodsRes.meta,
        extractedCandidatesRes.meta,
        normalizedSnapshotsRes.meta,
        coverageResponse.meta,
        reconciliationResponse.meta,
        identityResponse.meta,
        sourceFactsResponse.meta,
      ]} />
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Fundamentals: {company.ticker}</h1>
          <p className="text-muted-foreground">{company.name}</p>
        </div>
        <Link
          href={`/companies/${company.id}`}
          className="text-sm font-medium text-[var(--accent)] hover:text-[var(--accent)]"
        >
          &larr; Back to Dashboard
        </Link>
      </div>

      <DatedFinancialInputs report={hasUsableData(datedResponse) ? datedResponse.data : null}
        valuationDate={valuationDate} knowledge={knowledge} track={reviewTrack} error={datedResponse.errors[0]?.message} />
      <FinancialReviewPlanPanel report={hasUsableData(reviewPlanResponse) ? reviewPlanResponse.data : null}
        error={reviewPlanResponse.errors[0]?.message} track={reviewTrack} year={reviewYear} />

      <FinancialSourceHistory facts={hasUsableData(sourceFactsResponse) ? sourceFactsResponse.data : null}
        candidates={hasUsableData(extractedCandidatesRes) ? evidenceCandidates : []}
        error={sourceFactsResponse.errors[0]?.message} />

      <section className="border-y border-border bg-card px-4 py-5 sm:px-6" aria-labelledby="normalization-coverage-title">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 id="normalization-coverage-title" className="text-base font-semibold text-foreground">Normalization Coverage</h2>
            {coverage ? (
              <p className="mt-1 text-sm text-muted-foreground">
                {coverage.normalized_period_count} of {coverage.period_count} periods normalized ({coverage.coverage_percent}%).
                {" "}{coverage.trust_ready_period_count} periods pass normalization and currency checks.
                {" "}Complete valuation inputs still need review.
              </p>
            ) : (
              <p className="mt-1 text-sm text-[var(--danger)]">
                Coverage unavailable: {coverageResponse.errors[0]?.message || "Unknown API error"}
              </p>
            )}
          </div>
          {coverage && coverage.needs_backfill_count > 0 ? (
            <RetainedActionForm label="Backfill normalized financials" action={backfillNormalizedFinancialsAction}>
              <input type="hidden" name="company_id" value={companyId} />
              <button className="secondary-button" title="Backfill normalized financials" type="submit">
                <RefreshCw size={16} />
                Backfill {coverage.needs_backfill_count} period{coverage.needs_backfill_count === 1 ? "" : "s"}
              </button>
            </RetainedActionForm>
          ) : null}
        </div>
        {coverage && coverage.status !== "complete" && coverage.status !== "no_data" ? (
          <div className="mt-4 overflow-x-auto" role="region" aria-label="Financial normalization coverage" tabIndex={0}>
            <table className="min-w-full divide-y divide-border text-sm">
              <thead>
                <tr className="text-left text-muted-foreground">
                  <th className="py-2 pr-4 font-medium">Period</th>
                  <th className="px-4 py-2 font-medium">State</th>
                  <th className="px-4 py-2 font-medium">Currency evidence</th>
                  <th className="px-4 py-2 font-medium">Required action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {coverage.periods.filter((period) => period.needs_backfill || !period.trust_ready).map((period) => (
                  <tr key={period.period_id}>
                    <td className="py-2 pr-4 text-foreground">{period.period_type} {period.year}</td>
                    <td className="px-4 py-2 text-muted-foreground">{period.normalized_metric_count} normalized metrics</td>
                    <td className="px-4 py-2 text-muted-foreground">
                      {period.currency} / {period.currency_confidence} / {period.currency_source.replaceAll("_", " ")}
                    </td>
                    <td className="px-4 py-2 text-muted-foreground">
                      {period.currency_conflict || period.reasons.join(", ") || "Review currency provenance"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>

      <section className="border-y border-border bg-card px-4 py-5 sm:px-6" aria-labelledby="financial-reconciliation-title">
        <h2 id="financial-reconciliation-title" className="text-base font-semibold text-foreground">Source Reconciliation</h2>
        {reconciliation ? (
          <>
            <p className="mt-1 text-sm text-muted-foreground">
              Among comparable normalized metrics: {reconciliation.exact_count} exact matches, {reconciliation.mismatch_count} mismatches, and{" "}
              {reconciliation.missing_normalized_count + reconciliation.normalized_only_count} coverage gaps.
            </p>
            {reconciliationIssues.length > 0 ? (
              <div className="mt-4 overflow-x-auto" role="region" aria-label="Financial source reconciliation details" tabIndex={0}>
                <table className="min-w-full divide-y divide-border text-sm">
                  <thead>
                    <tr className="text-left text-muted-foreground">
                      <th className="py-2 pr-4 font-medium">Period</th>
                      <th className="px-4 py-2 font-medium">Metric</th>
                      <th className="px-4 py-2 font-medium">State</th>
                      <th className="px-4 py-2 font-medium">Source</th>
                      <th className="px-4 py-2 font-medium">Normalized</th>
                      <th className="px-4 py-2 font-medium">Delta</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {reconciliationIssues.map((item) => (
                      <tr key={`${item.period.period_id}-${item.metric_code}`}>
                        <td className="py-2 pr-4 text-foreground">{item.period.period_type} {item.period.year}</td>
                        <td className="px-4 py-2 text-foreground">{item.metric_code.replaceAll("_", " ")}</td>
                        <td className="px-4 py-2 text-[var(--warning)]">{item.status.replaceAll("_", " ")}</td>
                        <td className="px-4 py-2 text-muted-foreground">
                          {item.source_value === null ? "Missing" : item.source_value.toLocaleString()}
                        </td>
                        <td className="px-4 py-2 text-muted-foreground">
                          {item.normalized_value === null ? "Missing" : item.normalized_value.toLocaleString()}
                        </td>
                        <td className="px-4 py-2 text-muted-foreground">
                          {item.delta === null ? "-" : item.delta.toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : reconciliation.exact_count > 0 ? (
              <p className="mt-3 text-sm text-[var(--success)]">
                All comparable source metrics match the latest normalized snapshots.
              </p>
            ) : (
              <p className="mt-3 text-sm text-muted-foreground">
                No comparable reviewed metrics are available. Review and normalize source candidates before checking their agreement.
              </p>
            )}
          </>
        ) : (
          <p className="mt-1 text-sm text-[var(--danger)]">
            Reconciliation unavailable: {reconciliationResponse.errors[0]?.message || "Unknown API error"}
          </p>
        )}
      </section>

      <section className="border-y border-border bg-card px-4 py-5 sm:px-6" aria-labelledby="statement-identities-title">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 id="statement-identities-title" className="text-base font-semibold text-foreground">Statement Identities</h2>
            {identityReport ? (
              <p className="mt-1 text-sm text-muted-foreground">
                {identityReport.passed_check_count} passed, {identityReport.failed_check_count} failed, and{" "}
                {identityReport.unavailable_check_count} unavailable across {identityReport.period_count} annual periods.
              </p>
            ) : (
              <p className="mt-1 text-sm text-[var(--danger)]">
                Identity checks unavailable: {identityResponse.errors[0]?.message || "Unknown API error"}
              </p>
            )}
          </div>
          {identityReport ? (
            <span className={`rounded px-2 py-1 text-xs font-medium ${
              identityReport.status === "passed"
                ? "bg-[var(--success-bg)] text-[var(--success)]"
                : identityReport.status === "failed"
                  ? "bg-[var(--danger-bg)] text-[var(--danger)]"
                  : "bg-[var(--warning-bg)] text-[var(--warning)]"
            }`}>
              {identityReport.status.replaceAll("_", " ")}
            </span>
          ) : null}
        </div>
        {identityReport && identityReport.periods.length > 0 ? (
          <div className="mt-4 overflow-x-auto" role="region" aria-label="Financial statement identity checks" tabIndex={0}>
            <table className="min-w-full divide-y divide-border text-sm">
              <thead>
                <tr className="text-left text-muted-foreground">
                  <th className="py-2 pr-4 font-medium">Period</th>
                  <th className="px-4 py-2 font-medium">Identity</th>
                  <th className="px-4 py-2 font-medium">State</th>
                  <th className="px-4 py-2 font-medium">Actual</th>
                  <th className="px-4 py-2 font-medium">Expected</th>
                  <th className="px-4 py-2 font-medium">Delta / limitation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {identityReport.periods.flatMap((period) => period.checks.map((check) => (
                  <tr key={`${period.period_id}-${check.identity_code}`}>
                    <td className="py-2 pr-4 text-foreground">{period.period_type} {period.year}</td>
                    <td className="px-4 py-2 text-foreground">
                      {check.label}
                      <span className="block text-xs text-muted-foreground">{financialIdentityFormula(check.formula)}</span>
                      {check.actual_value !== null && <span className="block text-xs text-muted-foreground">Units: {check.unit}</span>}
                    </td>
                    <td className={`px-4 py-2 ${check.status === "passed" ? "text-[var(--success)]" : check.status === "failed" ? "text-[var(--danger)]" : "text-[var(--warning)]"}`}>
                      {check.status.replaceAll("_", " ")}
                    </td>
                    <td className="px-4 py-2 text-muted-foreground">
                      {check.actual_value === null ? "-" : check.actual_value.toLocaleString()}
                    </td>
                    <td className="px-4 py-2 text-muted-foreground">
                      {check.expected_value === null ? "-" : check.expected_value.toLocaleString()}
                    </td>
                    <td className="px-4 py-2 text-muted-foreground">
                      {check.delta !== null
                        ? `${check.delta.toLocaleString()} (tolerance ${check.tolerance?.toLocaleString()})`
                        : check.unit_issue ? check.unit_issue : check.ambiguous_metrics.length > 0
                          ? `Duplicate metrics: ${check.ambiguous_metrics.map(financialMetricLabel).join(", ")}`
                          : `Missing: ${check.missing_metrics.map(financialMetricLabel).join(", ")}`}
                    </td>
                  </tr>
                ))) }
              </tbody>
            </table>
          </div>
        ) : identityReport ? (
          <p className="mt-3 text-sm text-muted-foreground">No annual financial periods are available for identity checks.</p>
        ) : null}
      </section>

      <div className="bg-card shadow sm:rounded-lg overflow-hidden">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-base font-semibold leading-6 text-foreground">Financial Periods</h3>

          {company.market === "IN" && (
            <ScreenerUpload companyId={company.id} />
          )}

          <div className="mt-4 flow-root">
            <div className="-mx-4 -my-2 overflow-x-auto sm:-mx-6 lg:-mx-8" role="region" aria-label="Financial periods" tabIndex={0}>
              <div className="inline-block min-w-full py-2 align-middle sm:px-6 lg:px-8">
                {!hasUsableData(periodsRes) ? <ErrorState message="Financial periods could not be loaded. Reload to retry." /> : periods.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No financial periods found. (API ingestion needed)</p>
                ) : (
                  <table className="min-w-full divide-y divide-border">
                    <thead>
                      <tr>
                        <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-foreground">Period</th>
                        <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-foreground">Year</th>
                        <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-foreground">Quarter</th>
                        <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-foreground">Report Date</th>
                        <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-foreground">Currency</th>
                        <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-foreground">Metrics</th>
                        <th scope="col" className="relative py-3.5 pl-3 pr-4 sm:pr-0">
                          <span className="sr-only">Delete</span>
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {periods.map((period) => (
                        <tr key={period.id}>
                          <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-foreground">{period.period_type}</td>
                          <td className="whitespace-nowrap px-3 py-4 text-sm text-muted-foreground">{period.year}</td>
                          <td className="whitespace-nowrap px-3 py-4 text-sm text-muted-foreground">{period.quarter ?? "-"}</td>
                          <td className="whitespace-nowrap px-3 py-4 text-sm text-muted-foreground">{period.report_date}</td>
                          <td className="whitespace-nowrap px-3 py-4 text-sm text-muted-foreground">
                            {period.currency}
                            <span className="block text-xs">{period.currency_confidence} / {period.currency_source.replaceAll("_", " ")}</span>
                          </td>
                          <td className="whitespace-nowrap px-3 py-4 text-sm text-muted-foreground">
                            {period.metrics.length} metrics
                          </td>
                          <td className="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-0">
                            <div className="flex justify-end gap-3">
                              <RetainedActionForm label="Normalize financial period" action={normalizeFinancialPeriodAction}>
                                <input type="hidden" name="company_id" value={companyId} />
                                <input type="hidden" name="period_id" value={period.id} />
                                <button type="submit" className="text-[var(--accent)] hover:text-[var(--accent)]">
                                  Normalize
                                </button>
                              </RetainedActionForm>
                              <RetainedActionForm label="Review and save record" action={async (data) => {
                                "use server";
                                await deleteFinancialStatementPeriod(data, companyId.toString());
                              }}>
                                <input type="hidden" name="id" value={period.id} />
                                <button type="submit" className="text-[var(--danger)] hover:text-[var(--danger)]">
                                  Delete
                                </button>
                              </RetainedActionForm>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-card shadow sm:rounded-lg overflow-hidden">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-base font-semibold leading-6 text-foreground">Extracted Financial Candidates</h3>
              <p className="text-sm text-muted-foreground">Review these before using them in valuation.</p>
            </div>
            <Link href={`/companies/${company.id}/filings`} className="text-sm font-medium text-[var(--accent)] hover:text-[var(--accent)]">
              Manage filings
            </Link>
          </div>
          <div className="mt-4 flow-root">
            {hasUsableData(extractedCandidatesRes) ? <div id="financial-candidate-review"><FinancialCandidateReview initialCandidates={extractedCandidates} companyId={company.id} /></div>
              : <ErrorState message="Financial candidates could not be loaded. Reload to retry." />}
          </div>
        </div>
      </div>

      <div className="bg-card shadow sm:rounded-lg overflow-hidden">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-base font-semibold leading-6 text-foreground">Normalized Metrics</h3>
          <p className="text-sm text-muted-foreground">
            Check coverage and missing inputs before using these figures in a valuation.
          </p>
          <div className="mt-4 flow-root">
            <div className="-mx-4 -my-2 overflow-x-auto sm:-mx-6 lg:-mx-8" role="region" aria-label="Normalized financial metrics" tabIndex={0}>
              <div className="inline-block min-w-full py-2 align-middle sm:px-6 lg:px-8">
                {!hasUsableData(normalizedSnapshotsRes) ? <ErrorState message="Normalized metrics could not be loaded. Reload to retry." /> : normalizedSnapshots.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No normalized snapshots found. Click "Normalize" on a period above.</p>
                ) : (
                  <table className="min-w-full divide-y divide-border">
                    <thead>
                      <tr>
                        <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-foreground">Period</th>
                        <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-foreground">Values and basis</th>
                        <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-foreground">Last Updated</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {normalizedSnapshots.map((snapshot) => (
                        <tr key={snapshot.id}>
                          <td className="whitespace-nowrap py-4 pl-4 pr-3 align-top text-sm font-medium text-foreground">
                            {periods.find(period => period.id === snapshot.period_id)?.report_date ?? `Period ${snapshot.period_id}`}
                          </td>
                          <td className="px-3 py-4 align-top text-sm text-foreground">
                            {snapshot.metrics.length === 0 ? "No normalized metrics" : (
                              <details>
                                <summary className="cursor-pointer whitespace-nowrap font-medium text-[var(--accent)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--accent)]">
                                  Show {snapshot.metrics.length} metrics and their basis
                                </summary>
                                <dl className="mt-3 w-80 space-y-4 break-words sm:w-96">
                                  {snapshot.metrics.map(metric => (
                                    <div key={metric.id}>
                                      <dt className="font-semibold text-foreground">{metric.metric_code.replaceAll("_", " ")}</dt>
                                      <dd className="tabular-nums">{formatNumber(metric.value, 6)} {metric.unit ?? "Unit unavailable"}</dd>
                                      <dd className="mt-1 text-xs">{metric.provenance_notes || "Source basis unavailable. Review the original filing before use."}</dd>
                                      {metric.warnings && <dd className="mt-1 text-xs text-[var(--warning)]">Limitations: {metric.warnings}</dd>}
                                    </div>
                                  ))}
                                </dl>
                              </details>
                            )}
                          </td>
                          <td className="whitespace-nowrap px-3 py-4 text-sm text-muted-foreground">{new Date(snapshot.updated_at).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
