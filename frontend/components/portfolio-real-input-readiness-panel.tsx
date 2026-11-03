import { EmptyState, Panel } from "@/components/page";
import { DataStateNotices, MockDataBadge } from "@/components/ui/data-states";
import type { ApiMeta, PortfolioRealInputReadiness } from "@/lib/api";


function StatusBadge({ status }: { status: "passed" | "blocked" }) {
  const passed = status === "passed";
  return (
    <span
      style={{
        border: `1px solid ${passed ? "var(--success)" : "var(--error)"}`,
        borderRadius: "999px",
        color: passed ? "var(--success)" : "var(--error)",
        fontSize: "var(--font-size-xs)",
        fontWeight: 700,
        padding: "0.15rem 0.5rem",
      }}
    >
      {passed ? "Passed" : "Blocked"}
    </span>
  );
}

function ids(values: number[]) {
  return values.length ? values.join(", ") : "None";
}

export function PortfolioRealInputReadinessPanel({
  report,
  meta,
}: {
  report: PortfolioRealInputReadiness | null;
  meta: ApiMeta | null;
}) {
  return (
    <Panel title="Real-input portfolio smoke readiness">
      <DataStateNotices
        metas={[meta]}
        unavailableMessage="The real-input readiness audit could not be loaded. No readiness claim is being shown."
        mockMessage="Mock Data was detected in the required portfolio evidence. This portfolio is blocked from real-input certification."
      />

      {!report ? (
        <EmptyState label="Readiness is unavailable. Confirm backend readiness and reload this portfolio." />
      ) : (
        <>
          <div
            style={{
              alignItems: "flex-start",
              background: "var(--surface)",
              border: `1px solid ${report.certification_status === "ready" ? "var(--success)" : "var(--border)"}`,
              borderRadius: "8px",
              display: "flex",
              flexWrap: "wrap",
              gap: "0.75rem",
              justifyContent: "space-between",
              marginBottom: "1rem",
              padding: "1rem",
            }}
          >
            <div style={{ minWidth: 0 }}>
              <strong style={{ display: "block", fontSize: "1rem" }}>
                {report.certification_status === "ready"
                  ? "Ready for the manual real-input smoke"
                  : `${report.blockers.length} requirement(s) block the manual smoke`}
              </strong>
              <span style={{ color: "var(--text-secondary)", display: "block", fontSize: "0.84rem", lineHeight: 1.5, marginTop: "0.3rem" }}>
                Calculation through {report.as_of_date}. Readiness verifies persisted evidence, not an investment conclusion.
              </span>
            </div>
            <div style={{ alignItems: "center", display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
              {report.contains_mock_data ? <MockDataBadge /> : null}
              <StatusBadge status={report.certification_status === "ready" ? "passed" : "blocked"} />
            </div>
          </div>

          <div style={{ display: "grid", gap: "0.65rem", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 290px), 1fr))" }}>
            {report.checks.map((check) => (
              <article
                key={check.code}
                style={{
                  background: "var(--surface)",
                  border: "1px solid var(--border)",
                  borderRadius: "8px",
                  minWidth: 0,
                  padding: "0.9rem",
                }}
              >
                <div style={{ alignItems: "center", display: "flex", gap: "0.5rem", justifyContent: "space-between" }}>
                  <strong style={{ fontSize: "0.9rem" }}>{check.label}</strong>
                  <StatusBadge status={check.status} />
                </div>
                <p style={{ color: "var(--text-secondary)", fontSize: "0.8rem", lineHeight: 1.5, margin: "0.6rem 0 0" }}>
                  Required: {check.required}
                </p>
                <p style={{ fontSize: "0.8rem", lineHeight: 1.5, margin: "0.35rem 0 0", overflowWrap: "anywhere" }}>
                  Observed: {check.observed}
                </p>
                {check.status === "blocked" ? (
                  <p style={{ color: "var(--error)", fontSize: "0.8rem", lineHeight: 1.5, margin: "0.35rem 0 0" }}>
                    Next: {check.message}
                  </p>
                ) : null}
                <p style={{ color: "var(--text-secondary)", fontSize: "var(--font-size-xs)", margin: "0.55rem 0 0", overflowWrap: "anywhere" }}>
                  Record IDs: {ids(check.source_record_ids)}
                </p>
              </article>
            ))}
          </div>

          <details style={{ marginTop: "1rem" }}>
            <summary>Audit scope and source records</summary>
            <p style={{ color: "var(--text-secondary)", lineHeight: 1.55 }}>
              Period: {report.start_date || "Not available"} to {report.end_date || "Not available"}. Minimum aligned observations: {report.min_observations}. Lookback: {report.lookback_days} days.
            </p>
            <p>Snapshot IDs: {ids(report.source_snapshot_ids)}</p>
            <p>Market price IDs: {ids(report.source_market_price_ids)}</p>
            <p>FX observation IDs: {ids(report.source_fx_observation_ids)}</p>
            <p>DCF output IDs: {ids(report.source_dcf_output_ids)}</p>
          </details>
        </>
      )}
    </Panel>
  );
}
