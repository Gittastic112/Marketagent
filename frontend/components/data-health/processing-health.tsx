import { EmptyState, ErrorState, Panel } from "@/components/page";
import { hasUsableData } from "@/lib/data-state-meta";
import type { DataHealthData } from "@/lib/server/data-health";
import { formatDate, HealthMetric, statusBadge } from "./health-ui";

type ProcessingProps = Pick<DataHealthData, "processingRunsRes" | "sourcesRes" | "processingRuns" | "sources" | "byType" | "latestBySource" | "sourcesById">;
type SummaryProps = Pick<DataHealthData, "processingRunsRes" | "successRuns" | "failedRuns" | "totalFetched" | "totalCreated" | "totalErrors">;

export function OperationsSummary({ processingRunsRes, successRuns, failedRuns, totalFetched, totalCreated, totalErrors }: SummaryProps) {
  return (
      <section className="health-summary-section" aria-labelledby="operations-health-title">
        <div className="health-section-heading">
          <div>
            <h2 id="operations-health-title">Operations</h2>
            <p>Counts cover the latest 100 runs returned by the service, not the full history.</p>
          </div>
          {hasUsableData(processingRunsRes) ? <span>{totalFetched.toLocaleString()} records fetched in this window</span> : null}
        </div>
        {!hasUsableData(processingRunsRes) ? <ErrorState message="Processing runs could not be loaded." errors={processingRunsRes.errors} /> : <div className="health-metric-grid">
          <HealthMetric label="Successful runs" value={successRuns} tone="success" />
          <HealthMetric label="Failed runs" value={failedRuns} tone={failedRuns > 0 ? "danger" : "neutral"} />
          <HealthMetric label="Records created" value={totalCreated.toLocaleString()} />
          <HealthMetric label="Processing errors" value={totalErrors.toLocaleString()} tone={totalErrors > 0 ? "danger" : "neutral"} />
        </div>}
      </section>
  );
}

export function ProcessingHealthTables({ processingRunsRes, sourcesRes, processingRuns, sources, byType, latestBySource, sourcesById }: ProcessingProps) {
  return <>
      {/* Freshness by Ingestion Type */}
      <Panel title="Ingestion Freshness by Type">
        {!hasUsableData(processingRunsRes) ? <ErrorState message="Processing runs could not be loaded." errors={processingRunsRes.errors} /> : byType.size === 0 ? (
          <EmptyState label="No processing runs recorded yet." />
        ) : (
          <div tabIndex={0} className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Run Type</th>
                  <th>Runs in Window</th>
                  <th>Latest Run</th>
                  <th>Latest Status</th>
                  <th>Records Created</th>
                </tr>
              </thead>
              <tbody>
                {Array.from(byType.entries())
                  .sort((a, b) => Date.parse(b[1].latest.started_at) - Date.parse(a[1].latest.started_at))
                  .map(([type, summary]) => {
                    const { latest, createdCount: typeCreated } = summary;
                    return (
                      <tr key={type}>
                        <td><strong>{type}</strong></td>
                        <td>{summary.count}</td>
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
        {!hasUsableData(sourcesRes) ? <ErrorState message="Sources could not be loaded." errors={sourcesRes.errors} /> : sources.length === 0 ? (
          <EmptyState label="No sources configured." />
        ) : (
          <div tabIndex={0} className="table-wrap">
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
                  const latestRun = latestBySource.get(source.id);
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
                        {!hasUsableData(processingRunsRes) ? "Runs unavailable" : latestRun ? (
                          <span style={{ fontSize: "0.85rem" }}>
                            {statusBadge(latestRun.status)} {formatDate(latestRun.started_at)}
                          </span>
                        ) : (
                          <span style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>No runs in recent window</span>
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
        {!hasUsableData(processingRunsRes) ? <ErrorState message="Processing runs could not be loaded." errors={processingRunsRes.errors} /> : processingRuns.length === 0 ? (
          <EmptyState label="No processing runs recorded." />
        ) : (
          <div tabIndex={0} className="table-wrap">
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
  </>;
}
