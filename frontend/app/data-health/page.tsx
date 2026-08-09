import Link from "next/link";
import { applyEventEvidenceBackfill } from "@/app/actions";
import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { DataStateNotices } from "@/components/ui/data-states";
import { serverFetchApiResponse } from "@/lib/server-api";
import type {
  DamodaranCoverageReport,
  EventEvidenceBackfillReport,
  EvidenceIntegrityReport,
  ProcessingRun,
  ProviderHealth,
  Source,
  Alert,
} from "@/lib/api";

export const dynamic = "force-dynamic";

function formatDate(iso: string) {
  return new Date(iso).toLocaleString(undefined, { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

function statusBadge(status: string) {
  const colors: Record<string, string> = {
    success: "var(--success)",
    completed: "var(--success)",
    working: "var(--success)",
    configured: "var(--accent)",
    failed: "var(--error)",
    error: "var(--error)",
    failing: "var(--error)",
    running: "var(--warning)",
    missing_key: "var(--warning)",
    not_configured: "var(--warning)",
    not_available: "var(--text-secondary)",
    manual_only: "var(--text-secondary)",
    unsupported_market: "var(--text-secondary)",
    unknown: "var(--text-secondary)",
    pending: "var(--text-secondary)",
    healthy: "var(--success)",
    passed: "var(--success)",
    partial: "var(--warning)",
    supported: "var(--success)",
    unsupported: "var(--error)",
    ingested: "var(--success)",
    metadata_only: "var(--warning)",
    not_ingested: "var(--text-secondary)",
    source_missing: "var(--error)",
    current: "var(--success)",
    stale: "var(--warning)",
    historical: "var(--text-secondary)",
    user_assumed_recent: "var(--accent)",
    complete: "var(--success)",
    missing: "var(--warning)",
    hash_mismatch: "var(--error)",
    blocked: "var(--error)",
    issues_found: "var(--error)",
    eligible: "var(--warning)",
    applied: "var(--success)",
    ambiguous_match: "var(--warning)",
    mock: "var(--warning)",
    prototype: "var(--accent)",
  };
  const normalized = status.toLowerCase();
  const color = colors[normalized] ?? colors[normalized.split(" ").at(-1) ?? ""] ?? "var(--text-secondary)";
  return (
    <span className="badge" style={{ backgroundColor: `${color}20`, color, border: `1px solid ${color}40` }}>
      {status}
    </span>
  );
}

export default async function DataHealthPage() {
  try {
    const [processingRunsRes, sourcesRes, providerHealthRes, evidenceIntegrityRes, eventBackfillRes, damodaranCoverageRes, alertsRes] = await Promise.all([
      serverFetchApiResponse<ProcessingRun[]>("/processing-runs"),
      serverFetchApiResponse<Source[]>("/sources"),
      serverFetchApiResponse<ProviderHealth[]>("/api/providers/health"),
      serverFetchApiResponse<EvidenceIntegrityReport>("/data-health/evidence-integrity"),
      serverFetchApiResponse<EventEvidenceBackfillReport>("/data-health/event-evidence-backfill?limit=100"),
      serverFetchApiResponse<DamodaranCoverageReport>("/data-health/damodaran-coverage"),
      serverFetchApiResponse<Alert[]>("/alerts"),
    ]);

    const processingRuns = processingRunsRes.data || [];
    const sources = sourcesRes.data || [];
    const providerHealth = providerHealthRes.data || [];
    const evidenceIntegrity = evidenceIntegrityRes.data;
    const eventBackfill = eventBackfillRes.data;
    const damodaranCoverage = damodaranCoverageRes.data;
    const alerts = alertsRes.data || [];

    const unreviewedContradictions = alerts.filter((a: Alert) => a.alert_type === "contradiction" && a.review_status === "unreviewed");

    const sourcesById = new Map(sources.map(s => [s.id, s]));

    // Compute summary stats
    const totalRuns = processingRuns.length;
    const successRuns = processingRuns.filter(r => r.status === "success" || r.status === "completed").length;
    const failedRuns = processingRuns.filter(r => r.status === "failed" || r.status === "error").length;
    const totalFetched = processingRuns.reduce((sum, r) => sum + r.fetched_count, 0);
    const totalCreated = processingRuns.reduce((sum, r) => sum + r.created_count, 0);
    const totalErrors = processingRuns.reduce((sum, r) => sum + r.error_count, 0);
    const workingProviders = providerHealth.filter((provider) => provider.status === "working").length;
    const missingProviders = providerHealth.filter((provider) => provider.status === "missing_key" || provider.status === "not_configured").length;
    const failingProviders = providerHealth.filter((provider) => provider.status === "failing").length;

    // Group by run_type for freshness
    const byType = new Map<string, ProcessingRun[]>();
    for (const run of processingRuns) {
      const type = run.run_type || "unknown";
      if (!byType.has(type)) byType.set(type, []);
      byType.get(type)!.push(run);
    }

    return (
      <>
        <PageHeader eyebrow="System Health" title="Data Health" status={`${totalRuns} runs tracked`} />

        <DataStateNotices
          metas={[processingRunsRes.meta, sourcesRes.meta, providerHealthRes.meta, evidenceIntegrityRes.meta, eventBackfillRes.meta, damodaranCoverageRes.meta]}
          staleMessage="Showing cached data"
          mockMessage="Data health rows are mocked. Treat provider status as placeholder information."
        />

        {/* Summary Cards */}
        <section className="metric-grid" style={{ marginBottom: "2rem" }}>
          <div className="metric">
            <div className="metric-label">Successful Runs</div>
            <div className="metric-value" style={{ color: "var(--success)" }}>{successRuns}</div>
          </div>
          <div className="metric">
            <div className="metric-label">Failed Runs</div>
            <div className="metric-value" style={{ color: failedRuns > 0 ? "var(--error)" : undefined }}>{failedRuns}</div>
          </div>
          <div className="metric">
            <div className="metric-label">Records Created</div>
            <div className="metric-value">{totalCreated.toLocaleString()}</div>
          </div>
          <div className="metric">
            <div className="metric-label">Errors Encountered</div>
            <div className="metric-value" style={{ color: totalErrors > 0 ? "var(--error)" : undefined }}>{totalErrors.toLocaleString()}</div>
          </div>
        </section>

        <section className="metric-grid" style={{ marginBottom: "2rem" }}>
          <div className="metric">
            <div className="metric-label">Working Providers</div>
            <div className="metric-value" style={{ color: "var(--success)" }}>{workingProviders}</div>
          </div>
          <div className="metric">
            <div className="metric-label">Missing Configuration</div>
            <div className="metric-value" style={{ color: missingProviders > 0 ? "var(--warning)" : undefined }}>{missingProviders}</div>
          </div>
          <div className="metric">
            <div className="metric-label">Failing Providers</div>
            <div className="metric-value" style={{ color: failingProviders > 0 ? "var(--error)" : undefined }}>{failingProviders}</div>
          </div>
          <div className="metric">
            <div className="metric-label">Manual-Only Providers</div>
            <div className="metric-value">{providerHealth.filter((provider) => provider.status === "manual_only").length}</div>
          </div>
        </section>

        <section className="metric-grid" style={{ marginBottom: "2rem" }}>
          <div className="metric">
            <div className="metric-label">Evidence Errors</div>
            <div className="metric-value" style={{ color: evidenceIntegrity?.error_count ? "var(--error)" : "var(--success)" }}>
              {evidenceIntegrity?.error_count ?? 0}
            </div>
          </div>
          <div className="metric">
            <div className="metric-label">Evidence Warnings</div>
            <div className="metric-value" style={{ color: evidenceIntegrity?.warning_count ? "var(--warning)" : undefined }}>
              {evidenceIntegrity?.warning_count ?? 0}
            </div>
          </div>
          <div className="metric">
            <div className="metric-label">Documents Checked</div>
            <div className="metric-value">{evidenceIntegrity?.checked_documents ?? 0}</div>
          </div>
          <div className="metric">
            <div className="metric-label">Exact References Checked</div>
            <div className="metric-value">{evidenceIntegrity?.checked_references ?? 0}</div>
          </div>
        </section>

        <section className="metric-grid" style={{ marginBottom: "2rem" }}>
          <div className="metric">
            <div className="metric-label">Promoted Financial Facts</div>
            <div className="metric-value">{evidenceIntegrity?.checked_financial_candidates ?? 0}</div>
          </div>
          <div className="metric">
            <div className="metric-label">Annual Periods Checked</div>
            <div className="metric-value">{evidenceIntegrity?.checked_financial_periods ?? 0}</div>
          </div>
          <div className="metric">
            <div className="metric-label">Certified Histories</div>
            <div className="metric-value">{evidenceIntegrity?.certified_financial_history_count ?? 0}</div>
          </div>
          <div className="metric">
            <div className="metric-label">Certified Markets</div>
            <div className="metric-value" style={{ fontSize: "1.25rem" }}>
              {evidenceIntegrity?.certified_markets.join(", ") || "None"}
            </div>
          </div>
        </section>

        <Panel title="Unreviewed Contradiction Alerts" className="danger-panel">
          {unreviewedContradictions.length === 0 ? (
            <EmptyState label="No unreviewed contradictions found." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Company ID</th>
                    <th>Title</th>
                    <th>Summary</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {unreviewedContradictions.map((alert) => (
                    <tr key={alert.id}>
                      <td>{alert.id}</td>
                      <td>{alert.company_id ?? "Unlinked"}</td>
                      <td>{alert.title}</td>
                      <td>{alert.summary}</td>
                      <td>
                        <Link href={`/alerts/${alert.id}`} className="btn btn-secondary">Review</Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>

        <Panel title="Damodaran Application Coverage">
          {!damodaranCoverage ? (
            <ErrorState message="Damodaran application coverage is unavailable." />
          ) : (
            <>
              <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", alignItems: "flex-start", flexWrap: "wrap", marginBottom: "1rem" }}>
                <div>
                  <strong>{damodaranCoverage.ingested_count} of {damodaranCoverage.source_count} mirrored sources have typed database rows</strong>
                  <div style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginTop: "0.3rem" }}>
                    {damodaranCoverage.typed_record_count.toLocaleString()} typed records | inventory {damodaranCoverage.inventory_version}
                  </div>
                </div>
                <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
                  {statusBadge(`${damodaranCoverage.supported_count} supported`)}
                  {statusBadge(`${damodaranCoverage.partial_count} partial`)}
                  {statusBadge(`${damodaranCoverage.unsupported_count} unsupported`)}
                  {statusBadge(`${damodaranCoverage.provenance_complete_count} provenance complete`)}
                  {damodaranCoverage.provenance_hash_mismatch_count > 0 ? statusBadge(`${damodaranCoverage.provenance_hash_mismatch_count} hash_mismatch`) : null}
                  {damodaranCoverage.source_missing_count > 0 ? statusBadge(`${damodaranCoverage.source_missing_count} source_missing`) : null}
                </div>
              </div>

              {damodaranCoverage.warnings.length > 0 ? (
                <div className="notice notice-warning" style={{ marginBottom: "1rem" }}>
                  {damodaranCoverage.warnings.join(" ")}
                </div>
              ) : null}

              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Source</th>
                      <th>Metric Family</th>
                      <th>Implementation</th>
                      <th>Ingestion</th>
                      <th>Version Provenance</th>
                      <th>Freshness</th>
                      <th>Metric Coverage</th>
                      <th>Required Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {damodaranCoverage.rows.map((coverage) => (
                      <tr key={coverage.source_filename}>
                        <td style={{ minWidth: "12rem" }}>
                          <strong>{coverage.source_filename}</strong>
                          <div style={{ color: "var(--text-secondary)", fontSize: "0.78rem", marginTop: "0.2rem" }}>
                            {coverage.canonical_path}
                          </div>
                          <div style={{ color: "var(--text-secondary)", fontSize: "0.78rem", marginTop: "0.15rem" }}>
                            {coverage.claim_type} | {coverage.source_present ? "mirror present" : "mirror missing"}
                          </div>
                        </td>
                        <td>
                          <strong>{coverage.metric_family}</strong>
                          <div style={{ color: "var(--text-secondary)", fontSize: "0.8rem", marginTop: "0.2rem" }}>
                            {coverage.geography}
                          </div>
                        </td>
                        <td>
                          {statusBadge(coverage.implementation_status)}
                          <div style={{ color: "var(--text-secondary)", fontSize: "0.78rem", marginTop: "0.25rem" }}>
                            {coverage.destination_tables.join(", ") || "No typed destination"}
                          </div>
                        </td>
                        <td>
                          {statusBadge(coverage.ingestion_status)}
                          <div style={{ color: "var(--text-secondary)", fontSize: "0.78rem", marginTop: "0.25rem" }}>
                            {coverage.typed_record_count.toLocaleString()} typed rows
                          </div>
                        </td>
                        <td style={{ minWidth: "12rem" }}>
                          {statusBadge(coverage.provenance_status)}
                          <div style={{ color: "var(--text-secondary)", fontSize: "0.78rem", marginTop: "0.25rem" }}>
                            {coverage.active_version_id ? `Active #${coverage.active_version_id}` : "No active version"} | {coverage.stored_version_count} stored
                          </div>
                          <div style={{ color: coverage.hash_matches_mirror === false ? "var(--error)" : "var(--text-secondary)", fontFamily: "monospace", fontSize: "0.72rem", marginTop: "0.2rem" }}>
                            {coverage.active_source_sha256 ? coverage.active_source_sha256.slice(0, 12) : "No source hash"}
                            {coverage.hash_matches_mirror === true ? " | mirror match" : coverage.hash_matches_mirror === false ? " | mirror mismatch" : ""}
                          </div>
                        </td>
                        <td>
                          {statusBadge(coverage.freshness_status)}
                          <div style={{ color: "var(--text-secondary)", fontSize: "0.78rem", marginTop: "0.25rem" }}>
                            Source: {coverage.source_as_of} | {coverage.date_confidence} confidence
                          </div>
                        </td>
                        <td style={{ minWidth: "18rem", fontSize: "0.82rem" }}>
                          <div>
                            <strong>Stored:</strong> {coverage.supported_metrics.join(", ") || "None"}
                          </div>
                          <div style={{ color: coverage.missing_metrics.length > 0 ? "var(--warning)" : "var(--text-secondary)", marginTop: "0.3rem" }}>
                            <strong>Missing:</strong> {coverage.missing_metrics.join(", ") || "None"}
                          </div>
                          {coverage.limitations.length > 0 ? (
                            <div style={{ color: "var(--text-secondary)", marginTop: "0.3rem" }}>
                              {coverage.limitations.join(" ")}
                            </div>
                          ) : null}
                        </td>
                        <td style={{ minWidth: "15rem", color: "var(--text-secondary)", fontSize: "0.82rem" }}>
                          {coverage.action_required}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </Panel>

        <Panel title="Financial History Certification">
          {!evidenceIntegrity ? (
            <EmptyState label="Financial certification details are unavailable." />
          ) : evidenceIntegrity.financial_histories.length === 0 ? (
            <EmptyState label="No promoted financial histories are available for certification." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Company</th>
                    <th>Market</th>
                    <th>Certification</th>
                    <th>Normalization</th>
                    <th>Reconciliation</th>
                    <th>Identities</th>
                    <th>Evidence</th>
                    <th>Limits / failures</th>
                  </tr>
                </thead>
                <tbody>
                  {evidenceIntegrity.financial_histories.map((history) => (
                    <tr key={history.company_id}>
                      <td><Link href={`/companies/${history.company_id}/fundamentals`}><strong>{history.label || history.company}</strong></Link></td>
                      <td>{history.market}</td>
                      <td>{statusBadge(history.eligible_for_certification ? "passed" : "blocked")}</td>
                      <td>{statusBadge(history.coverage_status)}</td>
                      <td>{statusBadge(history.reconciliation_status)}</td>
                      <td>
                        {statusBadge(history.statement_identity_status)}
                        <div style={{ color: "var(--text-secondary)", fontSize: "0.8rem", marginTop: "0.2rem" }}>
                          {history.statement_identity_check_count} checked, {history.statement_identity_failed_count} failed
                        </div>
                      </td>
                      <td>{history.reviewed_evidence_count} facts / {history.period_count} periods</td>
                      <td style={{ color: history.failures.length > 0 ? "var(--error)" : "var(--text-secondary)", fontSize: "0.85rem" }}>
                        {[...history.failures, ...history.limitations].map((item) => item.replaceAll("_", " ")).join("; ") || "None"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>

        <Panel title="Evidence Integrity">
          {!evidenceIntegrity ? (
            <EmptyState label="Evidence integrity report is unavailable." />
          ) : evidenceIntegrity.issues.length === 0 ? (
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
              <div>
                <strong>No evidence integrity issues detected.</strong>
                <div style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginTop: "0.25rem" }}>
                  Checked {evidenceIntegrity.checked_documents} documents, {evidenceIntegrity.checked_assets} assets, {evidenceIntegrity.checked_references} exact references, and {evidenceIntegrity.checked_financial_candidates} promoted financial facts.
                </div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
                {statusBadge(evidenceIntegrity.status)}
                <span style={{ color: "var(--text-secondary)", fontSize: "0.8rem" }}>Financial certification</span>
                {statusBadge(evidenceIntegrity.financial_certification_status)}
              </div>
            </div>
          ) : (
            <>
              {evidenceIntegrity.is_truncated && (
                <div className="notice notice-warning" style={{ marginBottom: "0.75rem" }}>
                  Only the first {evidenceIntegrity.reported_issue_count} issues are shown. Resolve them and run the report again.
                </div>
              )}
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Severity</th>
                      <th>Check</th>
                      <th>Issue</th>
                      <th>Required Action</th>
                      <th>Source</th>
                    </tr>
                  </thead>
                  <tbody>
                    {evidenceIntegrity.issues.map((issue) => (
                      <tr key={`${issue.entity_type}-${issue.entity_id}-${issue.code}`}>
                        <td>{statusBadge(issue.severity)}</td>
                        <td><span className="badge">{issue.code}</span></td>
                        <td>{issue.message}</td>
                        <td style={{ color: "var(--text-secondary)" }}>{issue.action}</td>
                        <td>
                          {issue.document_id ? (
                            <Link href={`/documents/${issue.document_id}`}>Document {issue.document_id}</Link>
                          ) : (
                            `${issue.entity_type} ${issue.entity_id}`
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </Panel>

        <Panel title="Historical Event Evidence Backfill">
          {!eventBackfill ? (
            <ErrorState message="The historical evidence preview is unavailable." />
          ) : eventBackfill.entries.length === 0 ? (
            <EmptyState label="No unreferenced events are available in the current bounded batch." />
          ) : (
            <>
              <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", alignItems: "flex-start", flexWrap: "wrap", marginBottom: "1rem" }}>
                <div>
                  <strong>{eventBackfill.eligible_count} of {eventBackfill.checked_event_count} events are eligible</strong>
                  <p style={{ margin: "0.35rem 0 0", color: "var(--text-secondary)", fontSize: "0.85rem" }}>
                    Eligibility requires one exact case-sensitive occurrence in stored source text. Fuzzy matching is disabled.
                  </p>
                </div>
                {eventBackfill.eligible_count > 0 ? (
                  <form action={applyEventEvidenceBackfill}>
                    <button type="submit">Apply {eventBackfill.eligible_count} exact span{eventBackfill.eligible_count === 1 ? "" : "s"}</button>
                  </form>
                ) : null}
              </div>
              <div className="notice notice-warning" style={{ marginBottom: "1rem" }}>
                Apply creates evidence references only after the backend repeats the exact-match and duplicate checks. Ambiguous and unmatched events remain manual review work.
              </div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Priority</th>
                      <th>Event</th>
                      <th>Status</th>
                      <th>Exact claim</th>
                      <th>Required action</th>
                      <th>Source</th>
                    </tr>
                  </thead>
                  <tbody>
                    {eventBackfill.entries.map((entry) => (
                      <tr key={entry.event_id}>
                        <td>{entry.priority_score ?? "—"}</td>
                        <td><Link href={`/events?event_id=${entry.event_id}`}><strong>{entry.event_title}</strong></Link></td>
                        <td>{statusBadge(entry.status)}</td>
                        <td style={{ maxWidth: "28rem", fontSize: "0.85rem" }}>
                          {entry.quote ? (
                            <>
                              <div>{entry.quote}</div>
                              <div style={{ color: "var(--text-secondary)", marginTop: "0.2rem" }}>
                                {entry.claim_origin?.replaceAll("_", " ")} | characters {entry.start_char}-{entry.end_char}
                              </div>
                            </>
                          ) : "No unique exact claim"}
                        </td>
                        <td style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>
                          <div>{entry.action}</div>
                          {entry.raw_document_id && entry.status !== "eligible" && entry.status !== "missing_source_text" ? (
                            <Link
                              href={`/events/${entry.event_id}/evidence-resolution${entry.quote ? `?q=${encodeURIComponent(entry.quote)}` : ""}`}
                              style={{ display: "inline-block", marginTop: "0.35rem" }}
                            >
                              Resolve exact span
                            </Link>
                          ) : null}
                        </td>
                        <td>
                          {entry.raw_document_id ? (
                            <Link href={`/documents/${entry.raw_document_id}/sections`}>Document {entry.raw_document_id}</Link>
                          ) : "Unavailable"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </Panel>

        <Panel title="Provider Health">
          {providerHealth.length === 0 ? (
            <EmptyState label="No provider health information available." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Provider</th>
                    <th>Capability</th>
                    <th>Market</th>
                    <th>Coverage</th>
                    <th>Status</th>
                    <th>Freshness</th>
                    <th>Rate Limit</th>
                    <th>Latest Attempt</th>
                    <th>Last Success</th>
                    <th>Last Failure</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {providerHealth.map((provider) => (
                    <tr key={`${provider.provider_name}-${provider.capability}-${provider.market ?? "global"}`}>
                      <td>
                        <strong>{provider.provider_name}</strong>
                        {provider.notes && (
                          <div style={{ color: "var(--text-secondary)", fontSize: "0.8rem", marginTop: "0.2rem" }}>
                            {provider.notes}
                          </div>
                        )}
                      </td>
                      <td><span className="badge">{provider.capability}</span></td>
                      <td>{provider.market ?? "Global"}</td>
                      <td style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>{provider.coverage_state ?? "Unknown"}</td>
                      <td>{statusBadge(provider.status)}</td>
                      <td>{provider.freshness_label}</td>
                      <td style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>{provider.rate_limit_status ?? "Unknown"}</td>
                      <td style={{ fontSize: "0.85rem" }}>
                        {provider.last_attempt_at ? formatDate(provider.last_attempt_at) : "Never run"}
                        <div style={{ color: "var(--text-secondary)", fontSize: "0.8rem", marginTop: "0.2rem" }}>
                          {provider.latest_run_status ?? "No run evidence"} | {provider.recent_run_count} recorded run{provider.recent_run_count === 1 ? "" : "s"}
                        </div>
                        {provider.consecutive_failures > 0 && (
                          <div style={{ color: "var(--error)", fontSize: "0.8rem", marginTop: "0.2rem" }}>
                            {provider.consecutive_failures} consecutive failure{provider.consecutive_failures === 1 ? "" : "s"}
                          </div>
                        )}
                      </td>
                      <td style={{ fontSize: "0.85rem" }}>{provider.last_success_at ? formatDate(provider.last_success_at) : "—"}</td>
                      <td style={{ fontSize: "0.85rem" }}>
                        {provider.last_failure_at ? (
                          <>
                            {formatDate(provider.last_failure_at)}
                            {provider.failure_reason && (
                              <div style={{ color: "var(--error)", fontSize: "0.8rem", marginTop: "0.2rem" }}>
                                {provider.failure_reason}
                              </div>
                            )}
                          </>
                        ) : "—"}
                      </td>
                      <td style={{ color: provider.action_required ? "var(--text-secondary)" : "var(--success)", fontSize: "0.85rem" }}>
                        {provider.action_required ?? "No action needed"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Panel>

        {/* Freshness by Ingestion Type */}
        <Panel title="Ingestion Freshness by Type">
          {byType.size === 0 ? (
            <EmptyState label="No processing runs recorded yet." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Run Type</th>
                    <th>Total Runs</th>
                    <th>Latest Run</th>
                    <th>Latest Status</th>
                    <th>Records Created</th>
                  </tr>
                </thead>
                <tbody>
                  {Array.from(byType.entries())
                    .sort((a, b) => {
                      const aLatest = a[1][0]?.started_at ?? "";
                      const bLatest = b[1][0]?.started_at ?? "";
                      return bLatest.localeCompare(aLatest);
                    })
                    .map(([type, runs]) => {
                      const latest = runs[0];
                      const typeCreated = runs.reduce((sum, r) => sum + r.created_count, 0);
                      return (
                        <tr key={type}>
                          <td><strong>{type}</strong></td>
                          <td>{runs.length}</td>
                          <td>{latest ? formatDate(latest.started_at) : "—"}</td>
                          <td>{latest ? statusBadge(latest.status) : "—"}</td>
                          <td>{typeCreated.toLocaleString()}</td>
                        </tr>
                      );
                    })}
                </tbody>
              </table>
            </div>
          )}
        </Panel>

        {/* Active Sources Status */}
        <Panel title="Configured Sources">
          {sources.length === 0 ? (
            <EmptyState label="No sources configured." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Source</th>
                    <th>Type</th>
                    <th>Active</th>
                    <th>Reliability</th>
                    <th>Recent Runs</th>
                  </tr>
                </thead>
                <tbody>
                  {sources.map((source) => {
                    const sourceRuns = processingRuns.filter(r => r.source_id === source.id);
                    const latestRun = sourceRuns[0];
                    return (
                      <tr key={source.id}>
                        <td><strong>{source.name}</strong></td>
                        <td><span className="badge">{source.source_type}</span></td>
                        <td>
                          <span style={{ color: source.active ? "var(--success)" : "var(--text-secondary)" }}>
                            {source.active ? "●" : "○"} {source.active ? "Active" : "Inactive"}
                          </span>
                        </td>
                        <td>{source.reliability_score ?? "—"}</td>
                        <td>
                          {latestRun ? (
                            <span style={{ fontSize: "0.85rem" }}>
                              {statusBadge(latestRun.status)} {formatDate(latestRun.started_at)}
                            </span>
                          ) : (
                            <span style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>No runs</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Panel>

        {/* Recent Processing Runs */}
        <Panel title="Recent Processing Runs">
          {processingRuns.length === 0 ? (
            <EmptyState label="No processing runs recorded." />
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Run Type</th>
                    <th>Source</th>
                    <th>Status</th>
                    <th>Fetched</th>
                    <th>Created</th>
                    <th>Skipped</th>
                    <th>Errors</th>
                    <th>Started</th>
                    <th>Duration</th>
                  </tr>
                </thead>
                <tbody>
                  {processingRuns.slice(0, 25).map((run) => {
                    const source = run.source_id ? sourcesById.get(run.source_id) : null;
                    const durationMs = run.finished_at && run.started_at
                      ? new Date(run.finished_at).getTime() - new Date(run.started_at).getTime()
                      : null;
                    const durationLabel = durationMs != null
                      ? durationMs < 1000
                        ? `${durationMs}ms`
                        : `${(durationMs / 1000).toFixed(1)}s`
                      : "—";

                    return (
                      <tr key={run.id}>
                        <td><strong>{run.run_type}</strong></td>
                        <td>{source?.name ?? (run.source_type || "—")}</td>
                        <td>{statusBadge(run.status)}</td>
                        <td>{run.fetched_count}</td>
                        <td>{run.created_count}</td>
                        <td>{run.skipped_duplicate_count}</td>
                        <td style={{ color: run.error_count > 0 ? "var(--error)" : undefined }}>{run.error_count}</td>
                        <td style={{ fontSize: "0.85rem" }}>{formatDate(run.started_at)}</td>
                        <td style={{ fontSize: "0.85rem" }}>{durationLabel}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      </>
    );
  } catch {
    return (
      <>
        <PageHeader eyebrow="System Health" title="Data Health" />
        <ErrorState message="Could not load data health information from the backend." />
      </>
    );
  }
}
