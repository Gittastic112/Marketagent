import { EmptyState, ErrorState, Panel } from "@/components/page";
import { hasUsableData } from "@/lib/data-state-meta";
import type { DataHealthData } from "@/lib/server/data-health";
import { formatDate, HealthMetric, statusBadge } from "./health-ui";

type ProviderProps = Pick<DataHealthData, "providerHealthRes" | "providerHealth" | "workingProviders" | "missingCoreProviders" | "missingOptionalProviders" | "failingProviders">;

export function ProviderHealthSummary({ providerHealthRes, workingProviders, missingCoreProviders, missingOptionalProviders, failingProviders }: ProviderProps) {
  return (
      <section className="health-summary-section" aria-labelledby="provider-readiness-title">
        <div className="health-section-heading">
          <div>
            <h2 id="provider-readiness-title">Provider readiness</h2>
            <p>Required gaps are blockers. Optional connections are informational.</p>
          </div>
        </div>
        {!hasUsableData(providerHealthRes) ? <ErrorState message="Provider health could not be loaded." errors={providerHealthRes.errors} /> : <div className="health-metric-grid">
          <HealthMetric label="Working providers" value={workingProviders} tone="success" />
          <HealthMetric label="Required config gaps" value={missingCoreProviders} tone={missingCoreProviders > 0 ? "danger" : "success"} />
          <HealthMetric label="Failing providers" value={failingProviders} tone={failingProviders > 0 ? "danger" : "neutral"} />
          <HealthMetric label="Optional integrations" value={missingOptionalProviders} detail="Not configured" tone="muted" />
        </div>}
      </section>
  );
}

export function ProviderHealthTable({ providerHealthRes, providerHealth }: Pick<ProviderProps, "providerHealthRes" | "providerHealth">) {
  return (
      <Panel title="Provider Health">
        {!hasUsableData(providerHealthRes) ? <ErrorState message="Provider health could not be loaded." errors={providerHealthRes.errors} /> : providerHealth.length === 0 ? (
          <EmptyState label="No provider health information available." />
        ) : (
          <div tabIndex={0} className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Provider</th>
                  <th>Capability</th>
                  <th>Requirement</th>
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
                    <td>{statusBadge(provider.requirement_level)}</td>
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
  );
}
