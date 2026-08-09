import { ErrorState, PageHeader, Panel } from "@/components/page";
import { serverFetchApiResponse } from "@/lib/server-api";
import { DataStateNotices } from "@/components/ui/data-states";
import { RegimeInputForm } from "@/components/portfolio/RegimeInputForm";
import type { MarketRegimeScoreRead } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function MarketRegimePage() {
  try {
    const regimeRes = await serverFetchApiResponse<MarketRegimeScoreRead>("/market-regime/current");
    const score = regimeRes.data!;

    return (
      <>
        <PageHeader
          eyebrow="Portfolio"
          title="Market Regime"
          status="Macro & Liquidity conditions"
          badge={<span className="badge badge-outline">{score.mode}</span>}
        />

        <DataStateNotices
          metas={[regimeRes.meta]}
          mockMessage="Market Regime data is simulated or incomplete. Please provide metric inputs."
        />

        <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: "1.5rem", marginTop: "1.5rem" }}>

          {/* Left Column: Readiness Score */}
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <Panel title="Entry Timing Readiness">
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", padding: "2rem 0" }}>
                <div style={{
                  width: "140px",
                  height: "140px",
                  borderRadius: "50%",
                  border: "12px solid var(--warning)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "3rem",
                  fontWeight: 700,
                  color: "var(--text-primary)"
                }}>
                  {score.calculation_status === "blocked" ? "N/A" : Math.round(score.overall_score)}
                </div>
                <div style={{ marginTop: "1rem", fontWeight: 600, color: "var(--warning)", fontSize: "1.2rem" }}>
                  {score.mode}
                </div>
                <p style={{ textAlign: "center", color: "var(--text-secondary)", fontSize: "0.9rem", marginTop: "0.5rem" }}>
                  Confidence: {score.confidence}
                </p>
              </div>
            </Panel>

          <Panel title="Regime Data State">
             <div className="brief-list">
               <div className="brief-item">
                 <strong>Mode:</strong> <span>{score.mode}</span>
               </div>
               <div className="brief-item">
                 <strong>Confidence:</strong> <span>{score.confidence}</span>
               </div>
               <div className="brief-item">
                 <strong>Provider-backed modules:</strong> <span>{score.live_modules.length > 0 ? score.live_modules.join(", ") : "None"}</span>
               </div>
               <div className="brief-item">
                 <strong>Manual modules:</strong> <span>{score.manual_modules.length > 0 ? score.manual_modules.join(", ") : "None"}</span>
               </div>
             </div>
          </Panel>
        </div>

        {/* Right Column: Drivers & Evidence */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>

          <Panel title="Market Drivers (Modules)">
             <div className="table-wrap">
               <table>
                 <thead>
                   <tr>
                     <th>Metric Module</th>
                     <th>Weight</th>
                     <th>Value</th>
                   </tr>
                 </thead>
                 <tbody>
                   <tr>
                     <td>Options</td>
                     <td>30%</td>
                     <td>{score.options_score !== null ? score.options_score.toFixed(2) : <span style={{color: 'var(--warning)'}}>Missing</span>}</td>
                   </tr>
                   <tr>
                     <td>Liquidity</td>
                     <td>25%</td>
                     <td>{score.liquidity_score !== null ? score.liquidity_score.toFixed(2) : <span style={{color: 'var(--warning)'}}>Missing</span>}</td>
                   </tr>
                   <tr>
                     <td>Volume</td>
                     <td>15%</td>
                     <td>{score.volume_score !== null ? score.volume_score.toFixed(2) : <span style={{color: 'var(--warning)'}}>Missing</span>}</td>
                   </tr>
                   <tr>
                     <td>Breadth</td>
                     <td>15%</td>
                     <td>{score.breadth_score !== null ? score.breadth_score.toFixed(2) : <span style={{color: 'var(--warning)'}}>Missing</span>}</td>
                   </tr>
                   <tr>
                     <td>Macro</td>
                     <td>15%</td>
                     <td>{score.macro_score !== null ? score.macro_score.toFixed(2) : <span style={{color: 'var(--warning)'}}>Missing</span>}</td>
                   </tr>
                 </tbody>
               </table>
             </div>
             {score.warnings && score.warnings.map((w: string, i: number) => (
               <div key={i} style={{ color: "var(--warning)", fontSize: "0.85rem", marginTop: "1rem" }}>
                 ⚠️ {w}
               </div>
             ))}
             <div style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginTop: "1rem" }}>
               Calculation: {score.formula}
             </div>
             {score.blockers.map((blocker) => (
               <div key={blocker} style={{ color: "var(--danger)", fontSize: "0.85rem", marginTop: "0.5rem" }}>Blocked: {blocker}</div>
             ))}
          </Panel>

          <Panel title="Input Evidence & Freshness">
            {score.input_sources.length === 0 ? (
              <p style={{ color: "var(--text-secondary)" }}>No regime inputs are recorded.</p>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead><tr><th>Module</th><th>Type</th><th>Source</th><th>As Of</th><th>Freshness</th><th>Method</th></tr></thead>
                  <tbody>
                    {score.input_sources.map((source) => (
                      <tr key={source.input_id}>
                        <td>{source.metric_name}</td>
                        <td>{source.input_type === "manual" ? "User Assumption" : "Fact"}</td>
                        <td>{source.source_url ? <a href={source.source_url} rel="noreferrer" target="_blank">{source.source_name}</a> : source.source_name}</td>
                        <td>{source.as_of_date}</td>
                        <td>{source.age_days} days old, limit {source.freshness_threshold_days}</td>
                        <td>{source.methodology}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Panel>

          <Panel title="Submit Metric Data">
             <RegimeInputForm />
          </Panel>
        </div>
      </div>
    </>
  );
  } catch (error: any) {
    return (
      <>
        <PageHeader eyebrow="Portfolio" title="Market Regime" />
        <ErrorState message={`Could not load Market Regime data. ${error?.message || error}`} />
      </>
    );
  }
}
