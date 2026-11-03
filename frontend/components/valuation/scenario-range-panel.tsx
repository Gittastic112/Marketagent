"use client";

import { useCallback } from "react";
import { getDcfScenarios, type DcfAssumptionSet } from "@/lib/api";
import { useLatestResource } from "@/lib/use-latest-resource";
import { scenarioDisplay } from "@/lib/scenario-display";
import { DiagnosticPanel } from "@/components/valuation/diagnostic-panel";

export function ScenarioRangePanel({ modelId, assumptions, modelType }: { modelId: number; assumptions: DcfAssumptionSet; modelType?: string }) {
  const loader = useCallback(() => getDcfScenarios(modelId, assumptions.id),
    [modelId, assumptions.id, assumptions.updated_at]);
  const resource = useLatestResource(loader);
  const retry = () => { void resource.reload().catch(() => { /* Error is displayed below. */ }); };
  if (resource.status === "loading") return <p role="status">Calculating scenarios from saved assumptions...</p>;
  if (resource.status === "error") return <div role="alert"><p>{resource.error}</p><button type="button" onClick={retry}>Retry scenarios</button></div>;
  const rows = scenarioDisplay(resource.data ?? [], assumptions, modelType);
  return <section aria-label="Scenario valuation range">
    <h3>Scenario valuation range</h3>
    <p style={{ color: "var(--text-secondary)" }}>Estimates from deterministic shocks to saved User Assumptions, not probabilities or forecast returns. Unsaved edits are excluded. Currency: {assumptions.cash_flow_currency ?? "Not configured"}.</p>
    <button type="button" onClick={retry}>Recalculate scenarios</button>
    {!rows.length && <p>No scenarios returned. Retry or inspect the saved model.</p>}
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 240px), 1fr))", gap: "1rem", marginTop: "1rem" }}>
      {rows.map((row, index) => <article key={row.scenario_name + index} className="valuation-output-card" style={{ minWidth: 0, overflowWrap: "anywhere" }}>
        <h4>{row.scenario_name}</h4><p>{row.description}</p>
        <p>Estimate per share: <strong>{row.value}</strong></p>
        <p>Gap to saved comparison price: {row.gap}</p>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>Calculation: intrinsic value / saved price − 1. The saved price is a User Assumption, not a live quote.</p>
        {row.state.reasons.map(reason => <p key={reason}>{reason}</p>)}
        <details><summary>Diagnostics and calculation basis</summary>
          <p>Saved assumption #{assumptions.id}. Calculated: {row.output.created_at ?? "Not available"}. Transient scenario, not a saved output record.</p>
          <DiagnosticPanel warnings={row.state.diagnosticWarnings.map(w => ({ ...w, suggestedFix: w.suggestedFix ?? undefined, formula: w.formula ?? undefined }))} />
        </details>
      </article>)}
    </div>
  </section>;
}
