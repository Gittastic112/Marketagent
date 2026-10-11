import { EmptyState, Panel } from "@/components/page";
import { MockDataBadge, PartialDataNotice } from "@/components/ui/data-states";
import type { PortfolioRiskReturn } from "@/lib/api";


function percent(value: number | null, digits = 2) {
  return value == null ? "Not available" : `${(value * 100).toFixed(digits)}%`;
}

function coverage(value: number) {
  return `${value.toFixed(1)}% covered`;
}

function Metric({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <div style={{ minWidth: 0, padding: "1rem", border: "1px solid var(--border)", borderRadius: "8px", background: "var(--surface)" }}>
      <div style={{ color: "var(--text-secondary)", fontSize: "0.78rem", letterSpacing: "0.025em", textTransform: "uppercase" }}>{label}</div>
      <div style={{ fontSize: "1.35rem", fontWeight: 650, marginTop: "0.3rem" }}>{value}</div>
      <div style={{ color: "var(--text-secondary)", fontSize: "0.8rem", lineHeight: 1.45, marginTop: "0.35rem" }}>{detail}</div>
    </div>
  );
}

function ClaimBadge({ children }: { children: string }) {
  return (
    <span style={{ display: "inline-flex", border: "1px solid var(--border)", borderRadius: "999px", padding: "0.15rem 0.5rem", color: "var(--text-secondary)", fontSize: "var(--font-size-xs)", fontWeight: 600 }}>
      {children}
    </span>
  );
}

export function PortfolioRiskReturnPanel({ comparison }: { comparison: PortfolioRiskReturn | null }) {
  return (
    <Panel title="Marginal Risk & DCF Valuation Gap">
      {!comparison ? (
        <EmptyState label="Risk and valuation-gap comparison is unavailable. Add dated market prices, then retry." />
      ) : (
        <>
          {comparison.contains_mock_data && (
            <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", marginBottom: "1rem", color: "var(--text-secondary)" }}>
              <MockDataBadge />
              <span>These calculations use explicitly synthetic test inputs and are not investment evidence.</span>
            </div>
          )}
          {comparison.calculation_status !== "complete" && (
            <PartialDataNotice message="History, price freshness or trusted DCF coverage is incomplete. Inspect the dated evidence and warnings below; unavailable values are not estimates." />
          )}

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))", gap: "0.75rem" }}>
            <Metric
              label="Annualized volatility"
              value={percent(comparison.portfolio_volatility_annualized)}
              detail={`${comparison.risk_claim_type}. ${coverage(comparison.risk_covered_weight_percent)} from aligned daily base-currency returns.`}
            />
            <Metric
              label="Weighted DCF gap"
              value={percent(comparison.portfolio_expected_return_decimal)}
              detail={`${comparison.expected_return_claim_type}. ${coverage(comparison.expected_return_coverage_percent)}. This is not an annualized forecast.`}
            />
            <Metric
              label="History window"
              value={`${comparison.lookback_days} days`}
              detail={`${comparison.min_observations} aligned return observations required through ${comparison.as_of_date}.`}
            />
          </div>

          {(comparison.blockers.length > 0 || comparison.warnings.length > 0) && (
            <div style={{ marginTop: "1rem", padding: "0.9rem 1rem", border: "1px solid var(--border)", borderRadius: "8px", background: "var(--surface)" }}>
              {comparison.blockers.map((message) => (
                <div key={message} style={{ color: "var(--danger)", fontSize: "0.84rem", lineHeight: 1.5 }}>Blocked: {message}</div>
              ))}
              {comparison.warnings.map((message) => (
                <div key={message} style={{ color: "var(--warning)", fontSize: "0.84rem", lineHeight: 1.5 }}>Warning: {message}</div>
              ))}
            </div>
          )}

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 330px), 1fr))", gap: "0.75rem", marginTop: "1rem" }}>
            {comparison.holdings.map((holding) => (
              <article key={holding.holding_id} style={{ minWidth: 0, padding: "1rem", border: "1px solid var(--border)", borderRadius: "8px", background: "var(--surface)" }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "0.75rem", flexWrap: "wrap" }}>
                  <strong style={{ fontSize: "1rem" }}>{holding.ticker}</strong>
                  <div style={{ display: "flex", gap: "0.35rem", flexWrap: "wrap" }}>
                    <ClaimBadge>{holding.component_risk == null ? "Risk unavailable" : "Risk calculation"}</ClaimBadge>
                    <ClaimBadge>{holding.expected_return_claim_type}</ClaimBadge>
                  </div>
                </div>

                <p className="cell-secondary">Price as of {holding.latest_market_price_as_of || "not available"}{holding.is_stale_price ? ` · Stale (${holding.price_age_days} days)` : ""}</p>
                <dl style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "0.75rem 1rem", margin: "1rem 0 0" }}>
                  <div><dt style={{ color: "var(--text-secondary)", fontSize: "0.75rem" }}>Portfolio weight</dt><dd style={{ margin: "0.2rem 0 0", fontWeight: 600 }}>{percent(holding.portfolio_weight_decimal)}</dd></div>
                  <div><dt style={{ color: "var(--text-secondary)", fontSize: "0.75rem" }}>Historical return</dt><dd style={{ margin: "0.2rem 0 0", fontWeight: 600 }}>{percent(holding.historical_return_decimal)}</dd></div>
                  <div><dt style={{ color: "var(--text-secondary)", fontSize: "0.75rem" }}>Annualized volatility</dt><dd style={{ margin: "0.2rem 0 0", fontWeight: 600 }}>{percent(holding.annualized_volatility)}</dd></div>
                  <div><dt style={{ color: "var(--text-secondary)", fontSize: "0.75rem" }}>Component risk</dt><dd style={{ margin: "0.2rem 0 0", fontWeight: 600 }}>{percent(holding.component_risk)}</dd></div>
                  <div><dt style={{ color: "var(--text-secondary)", fontSize: "0.75rem" }}>Risk from +1% weight</dt><dd style={{ margin: "0.2rem 0 0", fontWeight: 600 }}>{percent(holding.marginal_volatility_for_one_percent)}</dd></div>
                  <div><dt style={{ color: "var(--text-secondary)", fontSize: "0.75rem" }}>DCF valuation gap</dt><dd style={{ margin: "0.2rem 0 0", fontWeight: 600 }}>{percent(holding.expected_return_decimal)}</dd></div>
                  <div><dt style={{ color: "var(--text-secondary)", fontSize: "0.75rem" }}>Return observations</dt><dd style={{ margin: "0.2rem 0 0", fontWeight: 600 }}>{holding.observation_count}</dd></div>
                  <div><dt style={{ color: "var(--text-secondary)", fontSize: "0.75rem" }}>Aligned observations</dt><dd style={{ margin: "0.2rem 0 0", fontWeight: 600 }}>{holding.aligned_observation_count || "Not available"}</dd></div>
                </dl>

                {holding.warnings.map((message) => (
                  <div key={message} style={{ color: "var(--warning)", fontSize: "0.78rem", lineHeight: 1.45, marginTop: "0.6rem", overflowWrap: "anywhere" }}>{message}</div>
                ))}
              </article>
            ))}
          </div>

          <details style={{ marginTop: "1rem" }}>
            <summary>Methods and source records</summary>
            <p style={{ color: "var(--text-secondary)", lineHeight: 1.55 }}>{comparison.risk_formula}</p>
            <p style={{ color: "var(--text-secondary)", lineHeight: 1.55 }}>{comparison.expected_return_formula}</p>
            <p>Market price IDs: {comparison.source_market_price_ids.join(", ") || "None"}</p>
            <p>FX observation IDs: {comparison.source_fx_observation_ids.join(", ") || "Identity conversion only"}</p>
            <p>DCF output IDs: {comparison.source_dcf_output_ids.join(", ") || "None"}</p>
          </details>
        </>
      )}
    </Panel>
  );
}
