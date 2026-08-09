"use client";

import { useState, useEffect } from "react";
import { RelativeValuationPanel } from "./valuation/relative-valuation-panel";
import {
  DcfAssumptionSet,
  DcfOutput,
  DcfProjectionYear,
  DcfSensitivityTable,
  RegressionPriorResponse,
  fetchDebtRatioPrior,
} from "@/lib/api";
import api from "@/lib/api";
import { buildDebtRatioPriorRequest } from "@/lib/regression-priors";
import { SelectField, TextAreaField, TextField } from "@/components/form-fields";
import { DiagnosticPanel, DiagnosticWarning } from "@/components/valuation/diagnostic-panel";
type Tab = "story" | "assumptions" | "valuation" | "relative-valuation" | "sensitivity" | "reverse-dcf" | "notes";

export function DcfForm({
  modelId,
  companyId,
  latestAssumptionSet
}: {
  modelId: number;
  companyId: number;
  latestAssumptionSet?: DcfAssumptionSet;
}) {
  const [activeTab, setActiveTab] = useState<Tab>("story");
  const [isPending, setIsPending] = useState(false);

  const tabs: { id: Tab; label: string }[] = [
    { id: "story", label: "Story" },
    { id: "assumptions", label: "Assumptions" },
    { id: "valuation", label: "Valuation" },
    { id: "relative-valuation", label: "Relative Valuation" },
    { id: "sensitivity", label: "Sensitivity" },
    { id: "reverse-dcf", label: "Reverse DCF" },
    { id: "notes", label: "Notes" },
  ];

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsPending(true);
    const formData = new FormData(e.currentTarget);
    const { createDcfAssumptionSet } = await import("@/app/actions");
    await createDcfAssumptionSet(formData, modelId.toString(), companyId.toString());
    setIsPending(false);
    setActiveTab("valuation"); // Jump to output after running
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>

      {/* Tab Navigation */}
      <div style={{ display: "flex", gap: "0.5rem", borderBottom: "1px solid var(--border-color)", paddingBottom: "0.5rem" }}>
        {tabs.map(t => (
          <button
            key={t.id}
            type="button"
            onClick={() => setActiveTab(t.id)}
            style={{
              padding: "0.5rem 1rem",
              background: activeTab === t.id ? "var(--accent)" : "transparent",
              color: activeTab === t.id ? "#fff" : "var(--text-primary)",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="form-grid">
        <input type="hidden" name="valuation_model_id" value={modelId} />

        {/* ACTION BAR */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", padding: "1rem", background: "var(--panel-bg)", border: "1px solid var(--border-color)", borderRadius: "8px" }}>
           <div style={{ display: "flex", gap: "1rem", alignItems: "flex-end" }}>
             <SelectField id="scenario" label="Scenario" name="scenario" defaultValue={latestAssumptionSet?.scenario || "Base"} required>
               <option value="Base">Base Case</option>
               <option value="Bull">Bull Case</option>
               <option value="Bear">Bear Case</option>
             </SelectField>
             <button type="submit" disabled={isPending} style={{ height: "42px", padding: "0 2rem" }}>
               {isPending ? "Running..." : "Run Valuation"}
             </button>
           </div>

           <div style={{ display: activeTab === "assumptions" ? "flex" : "none", alignItems: "flex-end" }}>
             <AutofillDamodaran companyId={companyId} />
           </div>
        </div>

        {/* STORY TAB */}
        <div style={{ display: activeTab === "story" ? "block" : "none" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
             <TextAreaField id="story_text" label="Company Story" name="story_text" placeholder="What is the overall narrative for this company?" defaultValue={latestAssumptionSet?.story_text || ""} rows={3} />
             <TextAreaField id="growth_story" label="Growth Story" name="growth_story" placeholder="How will they grow revenues?" defaultValue={latestAssumptionSet?.growth_story || ""} rows={2} />
             <TextAreaField id="margin_story" label="Margin Story" name="margin_story" placeholder="What is the path to profitability or maintaining margins?" defaultValue={latestAssumptionSet?.margin_story || ""} rows={2} />
             <TextAreaField id="risk_story" label="Risk Story" name="risk_story" placeholder="What could break this thesis?" defaultValue={latestAssumptionSet?.risk_story || ""} rows={2} />
          </div>
        </div>

        {/* ASSUMPTIONS TAB */}
        <div style={{ display: activeTab === "assumptions" ? "block" : "none" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "32px" }}>
            {/* Left Column */}
            <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>

              <div className="section-block">
                <h3 style={{ fontSize: "14px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--accent)", marginBottom: "16px", borderBottom: "1px solid var(--line)", paddingBottom: "8px" }}>Revenue & Growth</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                  <TextField id="starting_revenue" label="Starting Revenue (Base Year)" name="starting_revenue" type="number" step="0.01" defaultValue={latestAssumptionSet?.starting_revenue?.toString()} required />
                  <TextAreaField id="revenue_growth_years_json" label="Revenue Growth Rates (JSON)" name="revenue_growth_years_json" placeholder='{"1": 0.15, "2": 0.12, "3": 0.10}' defaultValue={latestAssumptionSet?.revenue_growth_years_json ? JSON.stringify(latestAssumptionSet.revenue_growth_years_json) : '{"1": 0.10, "2": 0.10, "3": 0.10, "4": 0.10, "5": 0.10}'} rows={2} />
                  <TextField id="projection_years" label="Projection Years" name="projection_years" type="number" defaultValue="10" required />
                </div>
              </div>

              <div className="section-block">
                <h3 style={{ fontSize: "14px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--accent)", marginBottom: "16px", borderBottom: "1px solid var(--line)", paddingBottom: "8px" }}>Margins & Reinvestment</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                    <TextField id="current_operating_margin" label="Current Margin" name="current_operating_margin" type="number" step="0.001" defaultValue={latestAssumptionSet?.current_operating_margin?.toString()} required />
                    <TextField id="target_operating_margin" label="Target Margin" name="target_operating_margin" type="number" step="0.001" defaultValue={latestAssumptionSet?.target_operating_margin?.toString()} required />
                  </div>
                  <TextField id="tax_rate" label="Effective Tax Rate" name="tax_rate" type="number" step="0.001" defaultValue={latestAssumptionSet?.tax_rate?.toString() || "0.21"} required />
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                    <TextField id="sales_to_capital_ratio" label="Sales to Capital" name="sales_to_capital_ratio" type="number" step="0.01" defaultValue={latestAssumptionSet?.sales_to_capital_ratio?.toString() || "1.5"} required />
                    <TextField id="starting_invested_capital" label="Starting Invested Cap" name="starting_invested_capital" type="number" step="0.01" defaultValue={latestAssumptionSet?.starting_invested_capital?.toString() || "0"} required />
                  </div>
                </div>
              </div>

              <div className="section-block">
                <h3 style={{ fontSize: "14px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--accent)", marginBottom: "16px", borderBottom: "1px solid var(--line)", paddingBottom: "8px" }}>Payout Diagnostics (FCFE / DDM)</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                    <TextField id="net_income" label="Net Income" name="net_income" type="number" step="0.01" defaultValue={latestAssumptionSet?.net_income?.toString()} />
                    <TextField id="capex" label="CapEx" name="capex" type="number" step="0.01" defaultValue={latestAssumptionSet?.capex?.toString()} />
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                    <TextField id="depreciation" label="Depreciation" name="depreciation" type="number" step="0.01" defaultValue={latestAssumptionSet?.depreciation?.toString()} />
                    <TextField id="change_in_nwc" label="Change in NWC" name="change_in_nwc" type="number" step="0.01" defaultValue={latestAssumptionSet?.change_in_nwc?.toString()} />
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                    <TextField id="new_debt_issued" label="New Debt Issued" name="new_debt_issued" type="number" step="0.01" defaultValue={latestAssumptionSet?.new_debt_issued?.toString()} />
                    <TextField id="debt_repaid" label="Debt Repaid" name="debt_repaid" type="number" step="0.01" defaultValue={latestAssumptionSet?.debt_repaid?.toString()} />
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                    <TextField id="dividends" label="Dividends Paid" name="dividends" type="number" step="0.01" defaultValue={latestAssumptionSet?.dividends?.toString()} />
                    <TextField id="buybacks" label="Stock Buybacks" name="buybacks" type="number" step="0.01" defaultValue={latestAssumptionSet?.buybacks?.toString()} />
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                    <TextField id="stock_issuances" label="Stock Issuances" name="stock_issuances" type="number" step="0.01" defaultValue={latestAssumptionSet?.stock_issuances?.toString()} />
                    <TextField id="company_age" label="Company Age (Years)" name="company_age" type="number" step="1" defaultValue={latestAssumptionSet?.company_age?.toString()} />
                  </div>
                </div>
              </div>

            </div>

            {/* Right Column */}
            <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>

              <div className="section-block">
                <h3 style={{ fontSize: "14px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--accent)", marginBottom: "16px", borderBottom: "1px solid var(--line)", paddingBottom: "8px" }}>Cost of Capital & Terminal</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                    <TextField id="wacc_start" label="Initial WACC" name="wacc_start" type="number" step="0.001" defaultValue={latestAssumptionSet?.wacc_start?.toString() || "0.10"} required />
                    <TextField id="wacc_terminal" label="Terminal WACC" name="wacc_terminal" type="number" step="0.001" defaultValue={latestAssumptionSet?.wacc_terminal?.toString() || "0.08"} required />
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                    <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                      <TextField id="debt_to_capital" label="Target Debt Ratio" name="debt_to_capital" type="number" step="0.001" defaultValue={latestAssumptionSet?.debt_to_capital?.toString()} />
                      <DebtRatioPriorSuggest targetField="debt_to_capital" />
                    </div>
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                    <TextField id="terminal_growth_rate" label="Terminal Growth" name="terminal_growth_rate" type="number" step="0.001" defaultValue={latestAssumptionSet?.terminal_growth_rate?.toString() || "0.025"} required />
                    <TextField id="terminal_roic" label="Terminal ROIC" name="terminal_roic" type="number" step="0.001" defaultValue={latestAssumptionSet?.terminal_roic?.toString() || "0.08"} required />
                  </div>
                </div>
              </div>

              <div className="section-block">
                <h3 style={{ fontSize: "14px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--accent)", marginBottom: "16px", borderBottom: "1px solid var(--line)", paddingBottom: "8px" }}>Bridge to Equity</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                    <TextField id="cash" label="Cash & Equivalents" name="cash" type="number" step="0.01" defaultValue={latestAssumptionSet?.cash?.toString() || "0"} required />
                    <TextField id="debt" label="Total Debt" name="debt" type="number" step="0.01" defaultValue={latestAssumptionSet?.debt?.toString() || "0"} required />
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                    <TextField id="minority_interests" label="Minority Interests" name="minority_interests" type="number" step="0.01" defaultValue={latestAssumptionSet?.minority_interests?.toString() || "0"} />
                    <TextField id="preferred_stock" label="Preferred Stock" name="preferred_stock" type="number" step="0.01" defaultValue={latestAssumptionSet?.preferred_stock?.toString() || "0"} />
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                    <TextField id="cross_holdings" label="Cross-Holdings" name="cross_holdings" type="number" step="0.01" defaultValue={latestAssumptionSet?.cross_holdings?.toString() || "0"} />
                    <TextField id="operating_leases" label="Operating Leases" name="operating_leases" type="number" step="0.01" defaultValue={latestAssumptionSet?.operating_leases?.toString() || "0"} />
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                    <TextField id="employee_options_value" label="Options Value" name="employee_options_value" type="number" step="0.01" defaultValue={latestAssumptionSet?.employee_options_value?.toString() || "0"} />
                    <TextField id="diluted_shares" label="Diluted Shares" name="diluted_shares" type="number" step="0.01" defaultValue={latestAssumptionSet?.diluted_shares?.toString()} required />
                  </div>
                  <TextField id="current_market_price" label="Current Market Price" name="current_market_price" type="number" step="0.01" defaultValue={latestAssumptionSet?.current_market_price?.toString()} required />
                </div>
              </div>

            </div>
          </div>
        </div>

      </form>

      {/* VALUATION TAB (Read Only) */}
      <div style={{ display: activeTab === "valuation" ? "block" : "none" }}>
        {!latestAssumptionSet ? (
          <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-secondary)" }}>
            No valuation has been run yet. Go to Assumptions and click "Run Valuation".
          </div>
        ) : (
          <ValuationOutputView aset={latestAssumptionSet} />
        )}
      </div>

      <div style={{ display: activeTab === "relative-valuation" ? "block" : "none" }}>
        <RelativeValuationPanel
          companyId={companyId.toString()}
          financials={{
            revenue: latestAssumptionSet?.starting_revenue || undefined,
            ebitda: (latestAssumptionSet?.starting_revenue || 0) * (latestAssumptionSet?.current_operating_margin || 0), // Proxy for EBITDA
            ebit: (latestAssumptionSet?.starting_revenue || 0) * (latestAssumptionSet?.current_operating_margin || 0),
            netIncome: latestAssumptionSet?.net_income || undefined,
            bookEquity: undefined,
            investedCapital: latestAssumptionSet?.starting_invested_capital || undefined,
            debt: latestAssumptionSet?.debt || undefined,
            cash: latestAssumptionSet?.cash || undefined,
            dilutedShares: latestAssumptionSet?.diluted_shares || undefined
          }}
        />
      </div>

      {/* SENSITIVITY TAB */}
      <div style={{ display: activeTab === "sensitivity" ? "block" : "none" }}>
        {!latestAssumptionSet?.sensitivity_tables?.length ? (
          <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-secondary)" }}>
            No sensitivity table generated yet. Run the valuation to generate one.
          </div>
        ) : (
          <SensitivityTableView table={latestAssumptionSet.sensitivity_tables[0]} />
        )}
      </div>

      {/* REVERSE DCF TAB */}
      <div style={{ display: activeTab === "reverse-dcf" ? "block" : "none" }}>
        <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-secondary)" }}>
          Reverse DCF solver coming soon.
        </div>
      </div>

      {/* NOTES TAB */}
      <div style={{ display: activeTab === "notes" ? "block" : "none" }}>
        <div style={{ padding: "2rem", textAlign: "center", color: "var(--text-secondary)" }}>
          Decision logs coming soon.
        </div>
      </div>

    </div>
  );
}

function ValuationOutputView({ aset }: { aset: DcfAssumptionSet }) {
  const out = aset.outputs;
  if (!out) return <div>No output available.</div>;

  const fmt = (n: number | null | undefined, decimals=2) => n != null ? n.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals }) : "—";
  const fmtLarge = (n: number | null | undefined) => {
    if (n == null) return "—";
    const abs = Math.abs(n);
    if (abs >= 1e12) return `$${(n / 1e12).toFixed(2)}T`;
    if (abs >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
    if (abs >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
    if (abs >= 1e3) return `$${(n / 1e3).toFixed(1)}K`;
    return `$${n.toFixed(2)}`;
  };
  const fmtPct = (n: number | null | undefined) => n != null ? `${(n * 100).toFixed(1)}%` : "—";

  // Use backend Diagnostics Engine warnings
  const warnings = out.warnings_json || [];
  const modelQualityScore = out.model_quality_score ?? Math.max(0, 100 - (warnings.length * 15));


  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
      {/* 7 KPI Cards */}
      <div className="metric-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))" }}>
        <div className="metric">
          <div className="metric-label">Intrinsic Value / Share</div>
          <div className="metric-value" style={{ color: "var(--accent)", fontSize: "1.75rem" }}>${fmt(out.intrinsic_value_per_share)}</div>
        </div>
        <div className="metric">
          <div className="metric-label">Current Market Price</div>
          <div className="metric-value">${fmt(out.current_market_price)}</div>
        </div>
        <div className="metric">
          <div className="metric-label">Upside / Downside</div>
          <div className="metric-value" style={{ color: out.upside_downside_pct && out.upside_downside_pct > 0 ? "var(--success)" : "var(--danger)" }}>
            {fmtPct(out.upside_downside_pct)}
          </div>
        </div>
        <div className="metric">
          <div className="metric-label">Enterprise Value</div>
          <div className="metric-value">{fmtLarge(out.enterprise_value)}</div>
        </div>
        <div className="metric">
          <div className="metric-label">Equity Value</div>
          <div className="metric-value">{fmtLarge(out.equity_value)}</div>
        </div>
        <div className="metric">
          <div className="metric-label">Terminal Value % of EV</div>
          <div className="metric-value">{fmtPct(out.terminal_value_pct_of_ev)}</div>
        </div>
        <div className="metric" style={{ border: "1px solid var(--accent-light)", background: "var(--surface-hover)" }}>
          <div className="metric-label">Model Quality Score</div>
          <div className="metric-value" style={{ color: modelQualityScore >= 80 ? "var(--success)" : "var(--warning)" }}>{modelQualityScore}/100</div>
        </div>
        {(out.fcfe_intrinsic_value_per_share || out.ddm_intrinsic_value_per_share) && (
          <div className="metric" style={{ gridColumn: "1 / -1", display: "flex", gap: "2rem", justifyContent: "space-around", padding: "1rem" }}>
             {out.fcfe_intrinsic_value_per_share && (
               <div style={{ textAlign: "center" }}>
                 <div className="metric-label">FCFE Model Value / Share</div>
                 <div className="metric-value" style={{ color: "var(--text)", fontSize: "1.2rem" }}>${fmt(out.fcfe_intrinsic_value_per_share)}</div>
               </div>
             )}
             {out.ddm_intrinsic_value_per_share && (
               <div style={{ textAlign: "center" }}>
                 <div className="metric-label">DDM Model Value / Share</div>
                 <div className="metric-value" style={{ color: "var(--text)", fontSize: "1.2rem" }}>${fmt(out.ddm_intrinsic_value_per_share)}</div>
               </div>
             )}
          </div>
        )}
      </div>

      {warnings.length > 0 && (
        <div style={{ padding: "1.5rem", borderRadius: "8px", border: "1px solid var(--border-color)", background: "var(--panel-bg)", boxShadow: "0 4px 12px rgba(0,0,0,0.05)" }}>
          <div style={{ fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", marginBottom: "1rem" }}>Model Diagnostics</div>
          <DiagnosticPanel warnings={warnings as DiagnosticWarning[]} />
        </div>
      )}

      {/* Projections Table */}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Year</th>
              <th style={{ textAlign: "right" }}>Revenue</th>
              <th style={{ textAlign: "right" }}>Growth</th>
              <th style={{ textAlign: "right" }}>EBIT Margin</th>
              <th style={{ textAlign: "right" }}>EBIT</th>
              <th style={{ textAlign: "right" }}>NOPAT</th>
              <th style={{ textAlign: "right" }}>Reinvestment</th>
              <th style={{ textAlign: "right" }}>FCFF</th>
              <th style={{ textAlign: "right" }}>ROIC</th>
              <th style={{ textAlign: "right" }}>WACC</th>
              <th style={{ textAlign: "right" }}>PV of FCFF</th>
            </tr>
          </thead>
          <tbody>
            {aset.projection_years?.map(py => (
              <tr key={py.year_index}>
                <td>{py.year_index}</td>
                <td style={{ textAlign: "right" }}>{fmtLarge(py.revenue)}</td>
                <td style={{ textAlign: "right" }}>{fmtPct(py.revenue_growth)}</td>
                <td style={{ textAlign: "right" }}>{fmtPct(py.ebit_margin)}</td>
                <td style={{ textAlign: "right" }}>{fmtLarge(py.ebit)}</td>
                <td style={{ textAlign: "right" }}>{fmtLarge(py.nopat)}</td>
                <td style={{ textAlign: "right" }}>{fmtLarge(py.reinvestment)}</td>
                <td style={{ textAlign: "right" }}>{fmtLarge(py.fcff)}</td>
                <td style={{ textAlign: "right" }}>{fmtPct(py.roic)}</td>
                <td style={{ textAlign: "right" }}>{fmtPct(py.wacc)}</td>
                <td style={{ textAlign: "right" }}>{fmtLarge(py.pv_fcff)}</td>
              </tr>
            ))}
            <tr style={{ borderTop: "2px solid var(--border-color)", fontWeight: 600 }}>
              <td colSpan={10}>Sum of PV of FCFFs</td>
              <td style={{ textAlign: "right" }}>{fmtLarge(out.sum_pv_fcff)}</td>
            </tr>
            <tr>
              <td colSpan={10}>PV of Terminal Value (Terminal Growth {fmtPct(aset.terminal_growth_rate)})</td>
              <td style={{ textAlign: "right" }}>{fmtLarge(out.pv_terminal_value)}</td>
            </tr>
            <tr style={{ fontWeight: 700, borderTop: "2px solid var(--border-color)", background: "var(--panel-bg)" }}>
              <td colSpan={10}>Enterprise Value</td>
              <td style={{ textAlign: "right" }}>{fmtLarge(out.enterprise_value)}</td>
            </tr>
          </tbody>
        </table>
      </div>

    </div>
  );
}

function SensitivityTableView({ table }: { table: DcfSensitivityTable }) {
  if (!table.x_axis_json || !table.y_axis_json || !table.values_json) return null;

  const yKeys = Object.keys(table.values_json).sort((a, b) => parseFloat(a) - parseFloat(b));
  // Find all x keys from the first y row to build column headers
  const firstRow = (table.values_json as Record<string, Record<string, number>>)[yKeys[0]] || {};
  const xKeys = Object.keys(firstRow).sort((a, b) => parseFloat(a) - parseFloat(b));

  const fmtCurrency = (n: number | null | undefined) => n != null ? `$${n.toFixed(2)}` : "—";
  const xName = (table.x_axis_json as any)?.name || "Terminal Growth";
  const yName = (table.y_axis_json as any)?.name || "WACC";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <h3 style={{ margin: 0, fontSize: "1.2rem" }}>Sensitivity: {yName} vs {xName}</h3>
      <div className="table-wrap">
        <table style={{ textAlign: "center" }}>
          <thead>
            <tr>
              <th style={{ background: "var(--panel-bg)", borderBottom: "2px solid var(--border-color)", fontWeight: 700 }}>
                {yName} &darr; \ {xName} &rarr;
              </th>
              {xKeys.map(x => (
                <th key={x} style={{ borderBottom: "2px solid var(--border-color)", fontWeight: 600 }}>
                  {x}%
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {yKeys.map(y => (
              <tr key={y}>
                <td style={{ fontWeight: 600, background: "var(--panel-bg)", textAlign: "left", paddingLeft: "1rem" }}>{y}%</td>
                {xKeys.map(x => {
                  const val = (table.values_json as any)[y][x];
                  // If this is the center cell (base case, typically middle index 1 in a 3x3 table)
                  const isBase = y === yKeys[1] && x === xKeys[1];
                  return (
                    <td key={x} style={{ background: isBase ? "var(--accent-light)" : undefined, fontWeight: isBase ? 700 : 400, color: isBase ? "var(--accent)" : undefined }}>
                      {fmtCurrency(val)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)", textAlign: "center" }}>
        * Highlighted cell represents the base case Intrinsic Value per Share.
      </div>
    </div>
  );
}

function AutofillDamodaran({ companyId }: { companyId: number }) {
  const [candidates, setCandidates] = useState<string[]>([]);
  const [selectedIndustry, setSelectedIndustry] = useState("");
  const [isPending, setIsPending] = useState(false);

  useEffect(() => {
    api.get<string[]>(`/industries/suggest?companyId=${companyId}&country=India`).then(res => {
      if (res.data && res.data.length > 0) {
        setCandidates(res.data);
        setSelectedIndustry(res.data[0]);
      }
    }).catch(console.error);
  }, [companyId]);

  const handleAutofill = async () => {
    if (!selectedIndustry) return;
    setIsPending(true);
    try {
      const res = await api.get<any>(`/assumption-priors?country=India&industry=${encodeURIComponent(selectedIndustry)}`);
      const priors = res.data;
      if (!priors) return;

      const setVal = (id: string, val: any) => {
        if (val == null) return;
        const el = document.getElementById(id) as HTMLInputElement;
        if (el) el.value = typeof val === "object" ? JSON.stringify(val) : val.toString();
      };

      if (priors.marginPriors) {
        setVal("target_operating_margin", priors.marginPriors.suggestedTargetMargin);
      }
      if (priors.reinvestmentPriors) {
        setVal("sales_to_capital_ratio", priors.reinvestmentPriors.suggestedSalesToCapital);
      }
      if (priors.returnPriors) {
        setVal("terminal_roic", priors.returnPriors.suggestedTerminalRoc);
      }
      if (priors.revenueGrowthPriors) {
        const growth = priors.revenueGrowthPriors.suggestedYears1To2;
        if (growth != null) {
          setVal("revenue_growth_years_json", {
            "1": growth, "2": growth, "3": growth, "4": growth, "5": growth
          });
        }
      }
      // capitalStructurePriors could set target debt ratio in the future
    } catch (e) {
      console.error(e);
    } finally {
      setIsPending(false);
    }
  };

  return (
    <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
      <select value={selectedIndustry} onChange={e => setSelectedIndustry(e.target.value)} style={{ padding: "8px", borderRadius: "4px", border: "1px solid var(--border-color)", background: "var(--bg)", color: "var(--text-primary)" }}>
        {candidates.map(c => <option key={c} value={c}>{c}</option>)}
        {!candidates.length && <option value="">Loading industries...</option>}
      </select>
      <button type="button" onClick={handleAutofill} disabled={isPending || !selectedIndustry} style={{ height: "38px", background: "var(--bg)", border: "1px solid var(--border-color)" }}>
        {isPending ? "Loading..." : "Autofill from Damodaran"}
      </button>
    </div>
  );
}

function DebtRatioPriorSuggest({ targetField }: { targetField: string }) {
  const [isOpen, setIsOpen] = useState(false);
  const [isPending, setIsPending] = useState(false);
  const [region, setRegion] = useState<"Global" | "US">("Global");
  const [expectedEpsGrowthPct, setExpectedEpsGrowthPct] = useState("");
  const [institutionalHoldingsPct, setInstitutionalHoldingsPct] = useState("");
  const [companyAgeYears, setCompanyAgeYears] = useState("");
  const [result, setResult] = useState<RegressionPriorResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchPrior = async () => {
    const taxRate = (document.getElementById("tax_rate") as HTMLInputElement | null)?.value ?? "";
    const ageFromAssumptions = (document.getElementById("company_age") as HTMLInputElement | null)?.value ?? "";
    const built = buildDebtRatioPriorRequest({
      effectiveTaxRate: taxRate,
      expectedEpsGrowthPct,
      institutionalHoldingsPct,
      companyAgeYears: companyAgeYears || ageFromAssumptions,
      region,
    });
    if (!built.payload) {
      setError(built.error);
      setResult(null);
      return;
    }

    setIsPending(true);
    setError(null);
    try {
      setResult(await fetchDebtRatioPrior(built.payload));
    } catch {
      setResult(null);
      setError("Regression prior is unavailable.");
    } finally {
      setIsPending(false);
    }
  };

  const applySuggestion = () => {
    if (result?.prior_value == null || result.prior_value > 1) return;
    const el = document.getElementById(targetField) as HTMLInputElement;
    if (el) {
      el.value = result.prior_value.toFixed(6);
      el.dispatchEvent(new Event("input", { bubbles: true }));
      el.dispatchEvent(new Event("change", { bubbles: true }));
    }
  };

  const fieldStyle = {
    width: "100%",
    minWidth: 0,
    padding: "6px 8px",
    border: "1px solid var(--border-color)",
    borderRadius: "4px",
    background: "var(--bg)",
    color: "var(--text-primary)",
  } as const;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "0.8rem", marginTop: "-4px" }}>
      <button
        type="button"
        onClick={() => setIsOpen(value => !value)}
        aria-expanded={isOpen}
        style={{ alignSelf: "flex-start", padding: "3px 7px", fontSize: "0.75rem", background: "var(--panel-bg)", border: "1px solid var(--border-color)", cursor: "pointer" }}
      >
        Regression prior
      </button>
      {isOpen && (
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: "8px" }}>
            <label>
              <span>Region</span>
              <select value={region} onChange={event => setRegion(event.target.value as "Global" | "US")} style={fieldStyle}>
                <option value="Global">Global</option>
                <option value="US">US</option>
              </select>
            </label>
            <label>
              <span>Expected EPS growth (%)</span>
              <input type="number" step="0.1" value={expectedEpsGrowthPct} onChange={event => setExpectedEpsGrowthPct(event.target.value)} style={fieldStyle} />
            </label>
            <label>
              <span>Institutional holdings (%)</span>
              <input type="number" step="0.1" value={institutionalHoldingsPct} onChange={event => setInstitutionalHoldingsPct(event.target.value)} style={fieldStyle} />
            </label>
            <label>
              <span>Company age (years)</span>
              <input type="number" step="1" value={companyAgeYears} onChange={event => setCompanyAgeYears(event.target.value)} style={fieldStyle} />
            </label>
          </div>
          <button type="button" onClick={fetchPrior} disabled={isPending} style={{ alignSelf: "flex-start" }}>
            {isPending ? "Calculating..." : "Calculate estimate"}
          </button>
          {error && <div role="alert" style={{ color: "var(--danger)" }}>{error}</div>}
          {result && (
            <div aria-live="polite" style={{ display: "flex", flexDirection: "column", gap: "4px", color: "var(--text-secondary)" }}>
              <span>
                {result.claim_type} | {result.source_as_of} | adjusted R2 {result.adjusted_r_squared.toFixed(3)}
              </span>
              {result.prior_value != null && (
                <span>
                  Prior: <strong style={{ color: "var(--accent)" }}>{(result.prior_value * 100).toFixed(2)}%</strong>{" "}
                  <button type="button" onClick={applySuggestion} disabled={result.prior_value > 1}>Apply</button>
                </span>
              )}
              {result.warnings.map(warning => <span key={warning}>{warning}</span>)}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
