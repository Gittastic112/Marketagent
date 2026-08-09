import type { ValuationCompanyContext } from "@/lib/api";

export function MarketContextPanel({ context }: { context: ValuationCompanyContext }) {
  if (!context) return null;

  return (
    <div style={{ background: "var(--panel-bg)", padding: "1.5rem", borderRadius: "8px", border: "1px solid var(--border-color)", marginBottom: "2rem" }}>
      <div style={{ fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", marginBottom: "1rem" }}>
        Market Context & Defaults
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "1.5rem", marginBottom: context.warnings?.length > 0 ? "1.5rem" : "0" }}>
        <div>
          <div style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: "0.25rem" }}>Market</div>
          <div style={{ fontWeight: 600 }}>{context.market}</div>
        </div>
        <div>
          <div style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: "0.25rem" }}>Country</div>
          <div style={{ fontWeight: 600 }}>{context.country}</div>
        </div>
        <div>
          <div style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: "0.25rem" }}>Default Currency</div>
          <div style={{ fontWeight: 600 }}>{context.default_currency}</div>
        </div>
        <div>
          <div style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: "0.25rem" }}>Recommended Benchmark</div>
          <div style={{ fontWeight: 600 }}>{context.recommended_benchmark_country}</div>
        </div>
      </div>

      {context.warnings && context.warnings.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
          {context.warnings.map((warning, idx) => (
            <div key={idx} style={{ padding: "0.75rem", background: "rgba(245,158,11,0.1)", borderLeft: "4px solid var(--warning)", borderRadius: "0 4px 4px 0", fontSize: "0.85rem" }}>
              <strong>Note:</strong> {warning}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
