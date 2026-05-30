import { EmptyState, ErrorState, PageHeader, Panel } from "@/components/page";
import { fetchApi } from "@/lib/api";
import type { ProcessingRun, Source } from "@/lib/api";

export const dynamic = "force-dynamic";

function formatDate(iso: string) {
  return new Date(iso).toLocaleString(undefined, { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

function statusBadge(status: string) {
  const colors: Record<string, string> = {
    success: "var(--success)",
    completed: "var(--success)",
    failed: "var(--error)",
    error: "var(--error)",
    running: "var(--warning)",
    pending: "var(--text-secondary)",
  };
  const color = colors[status.toLowerCase()] ?? "var(--text-secondary)";
  return (
    <span className="badge" style={{ backgroundColor: `${color}20`, color, border: `1px solid ${color}40` }}>
      {status}
    </span>
  );
}

export default async function DataHealthPage() {
  try {
    const [processingRuns, sources] = await Promise.all([
      fetchApi<ProcessingRun[]>("/processing-runs"),
      fetchApi<Source[]>("/sources").catch(() => []),
    ]);

    const sourcesById = new Map(sources.map(s => [s.id, s]));

    // Compute summary stats
    const totalRuns = processingRuns.length;
    const successRuns = processingRuns.filter(r => r.status === "success" || r.status === "completed").length;
    const failedRuns = processingRuns.filter(r => r.status === "failed" || r.status === "error").length;
    const totalFetched = processingRuns.reduce((sum, r) => sum + r.fetched_count, 0);
    const totalCreated = processingRuns.reduce((sum, r) => sum + r.created_count, 0);
    const totalErrors = processingRuns.reduce((sum, r) => sum + r.error_count, 0);

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
