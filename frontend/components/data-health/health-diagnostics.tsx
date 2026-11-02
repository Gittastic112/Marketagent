import Link from "next/link";
import { applyEventEvidenceBackfill } from "@/app/actions";
import { EmptyState, ErrorState, Panel } from "@/components/page";
import type { DataHealthData } from "@/lib/server/data-health";
import { HealthMetric, statusBadge } from "./health-ui";

type DiagnosticProps = Pick<DataHealthData, "evidenceIntegrityRes" | "eventBackfillRes" | "damodaranCoverageRes" | "evidenceIntegrity" | "eventBackfill" | "damodaranCoverage">;

export function HealthDiagnosticSummary({ evidenceIntegrityRes, evidenceIntegrity }: Pick<DiagnosticProps, "evidenceIntegrityRes" | "evidenceIntegrity">) {
  const unavailableLabel = evidenceIntegrityRes ? "Unavailable" : "Not run";
  return (
      <section className="health-summary-section health-diagnostic-summary" aria-labelledby="diagnostic-status-title">
        <div className="health-section-heading">
          <div>
            <h2 id="diagnostic-status-title">Diagnostic status</h2>
            <p>These values remain unavailable until the explicit evidence audit runs.</p>
          </div>
          {!evidenceIntegrity ? <Link prefetch={false} href="/data-health?audit=evidence">Run audit</Link> : null}
        </div>
        <div className="health-diagnostic-grid">
          <HealthMetric compact label="Evidence errors" value={evidenceIntegrity ? evidenceIntegrity.error_count : unavailableLabel} tone={!evidenceIntegrity ? "muted" : evidenceIntegrity.error_count > 0 ? "danger" : "success"} />
          <HealthMetric compact label="Evidence warnings" value={evidenceIntegrity ? evidenceIntegrity.warning_count : unavailableLabel} tone={!evidenceIntegrity ? "muted" : evidenceIntegrity.warning_count > 0 ? "warning" : "neutral"} />
          <HealthMetric compact label="Documents checked" value={evidenceIntegrity ? evidenceIntegrity.checked_documents : unavailableLabel} tone={evidenceIntegrity ? "neutral" : "muted"} />
          <HealthMetric compact label="Exact references" value={evidenceIntegrity ? evidenceIntegrity.checked_references : unavailableLabel} tone={evidenceIntegrity ? "neutral" : "muted"} />
          <HealthMetric compact label="Financial facts" value={evidenceIntegrity ? evidenceIntegrity.checked_financial_candidates : unavailableLabel} tone={evidenceIntegrity ? "neutral" : "muted"} />
          <HealthMetric compact label="Annual periods" value={evidenceIntegrity ? evidenceIntegrity.checked_financial_periods : unavailableLabel} tone={evidenceIntegrity ? "neutral" : "muted"} />
          <HealthMetric compact label="Certified histories" value={evidenceIntegrity ? evidenceIntegrity.certified_financial_history_count : unavailableLabel} tone={evidenceIntegrity ? "neutral" : "muted"} />
          <HealthMetric compact label="Certified markets" value={evidenceIntegrity ? evidenceIntegrity.certified_markets.join(", ") || "None" : unavailableLabel} tone={evidenceIntegrity ? "neutral" : "muted"} />
        </div>
      </section>
  );
}

export function HealthDiagnostics({ evidenceIntegrityRes, eventBackfillRes, damodaranCoverageRes, evidenceIntegrity, eventBackfill, damodaranCoverage }: DiagnosticProps) {
  return <>
      <Panel title="Damodaran Application Coverage">
        {!damodaranCoverageRes ? (
          <div className="empty">
            Coverage reconciliation is not run during the fast health check. <Link prefetch={false} href="/data-health?audit=coverage">Check benchmark coverage</Link>.
          </div>
        ) : !damodaranCoverage ? (
          <ErrorState message="Damodaran application coverage is unavailable." errors={damodaranCoverageRes.errors} />
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

            <div tabIndex={0} className="table-wrap">
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
        {!evidenceIntegrityRes ? (
          <div className="empty">
            Financial certification is part of the explicit evidence audit. <Link prefetch={false} href="/data-health?audit=evidence">Run deep evidence audit</Link>.
          </div>
        ) : !evidenceIntegrity ? (
          <ErrorState message="Financial certification details are unavailable." errors={evidenceIntegrityRes.errors} />
        ) : evidenceIntegrity.financial_histories.length === 0 ? (
          <EmptyState label="No promoted financial histories are available for certification." />
        ) : (
          <div tabIndex={0} className="table-wrap">
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
        {!evidenceIntegrityRes ? (
          <div className="empty">
            Deep asset and exact-reference verification is not run automatically. <Link prefetch={false} href="/data-health?audit=evidence">Run deep evidence audit</Link>.
          </div>
        ) : !evidenceIntegrity ? (
          <ErrorState message="Evidence integrity report is unavailable." errors={evidenceIntegrityRes.errors} />
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
            <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap", marginBottom: "0.75rem" }}>
              {statusBadge(evidenceIntegrity.verification_scope)}
              <span style={{ color: "var(--text-secondary)", fontSize: "0.82rem" }}>
                Asset content verification: {evidenceIntegrity.asset_content_verification_status.replaceAll("_", " ")}
              </span>
            </div>
            {evidenceIntegrity.limitations.length > 0 ? (
              <div className="notice notice-warning" style={{ marginBottom: "0.75rem" }}>
                {evidenceIntegrity.limitations.join(" ")}
              </div>
            ) : null}
            {evidenceIntegrity.is_truncated && (
              <div className="notice notice-warning" style={{ marginBottom: "0.75rem" }}>
                Only the first {evidenceIntegrity.reported_issue_count} issues are shown. Resolve them and run the report again.
              </div>
            )}
            <div tabIndex={0} className="table-wrap">
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
        {!eventBackfillRes ? (
          <div className="empty">
            Historical backfill preview is not run automatically. <Link prefetch={false} href="/data-health?audit=backfill">Preview evidence backfill</Link>.
          </div>
        ) : !eventBackfill ? (
          <ErrorState message="The historical evidence preview is unavailable." errors={eventBackfillRes.errors} />
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
            <div tabIndex={0} className="table-wrap">
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
  </>;
}
