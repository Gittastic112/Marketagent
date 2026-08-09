"use client";

import { useState } from "react";
import { DcfAssumptionSet, DcfOutput, ReverseDcfResponse, ValuationCompanyContext, ValuationModel } from "@/lib/api";
import { SelectField, TextField, TextAreaField } from "@/components/form-fields";
import { buildCurrencyConsistencyCheck } from "@/lib/valuation-context";
import { CurrencyConsistencyWarning } from "@/components/valuation/currency-consistency-warning";
import { MacroSensitivityPanel } from "@/components/valuation/macro-sensitivity-panel";
import { NarrativeToNumbersPanel } from "@/components/valuation/narrative-to-numbers-panel";
import { ValuationMemoPanel } from "@/components/valuation/valuation-memo-panel";
import { RelativeValuationPanel } from "@/components/valuation/relative-valuation-panel";
import { SensitivityTablesPanel } from "@/components/valuation/sensitivity-tables-panel";
import { ScenarioRangePanel } from "@/components/valuation/scenario-range-panel";
import { RealOptionsPanel } from "@/components/valuation/real-options-panel";
import { ValuationChangeLogPanel } from "@/components/valuation/valuation-change-log-panel";
import { DiagnosticPanel, DiagnosticWarning } from "@/components/valuation/diagnostic-panel";
import { NotConfiguredState, DataFreshnessIndicator } from "@/components/ui/data-states";
import { formatCurrency } from "@/lib/formatting";

type Section =
  | "setup"
  | "lifecycle"
  | "story"
  | "revenue"
  | "margins"
  | "reinvestment"
  | "cost_of_capital"
  | "terminal_value"
  | "payouts"
  | "equity_bridge"
  | "macro_sensitivity"
  | "sensitivity_tables"
  | "relative_valuation"
  | "scenario_range"
  | "real_options"
  | "narrative_to_numbers"
  | "valuation_memo"
  | "market_intelligence"
  | "reverse_dcf";

const SECTION_GROUPS: Array<{ label: string; sections: Array<{ id: Section; label: string }> }> = [
  {
    label: "Model",
    sections: [
      { id: "setup", label: "Setup & Scenario" },
      { id: "story", label: "Thesis & Story" },
      { id: "lifecycle", label: "Lifecycle & Special" },
    ],
  },
  {
    label: "Core assumptions",
    sections: [
      { id: "revenue", label: "Revenue & Growth" },
      { id: "margins", label: "Operating Margins" },
      { id: "reinvestment", label: "Reinvestment & Taxes" },
      { id: "cost_of_capital", label: "Cost of Capital" },
      { id: "terminal_value", label: "Terminal Value" },
      { id: "equity_bridge", label: "Equity Bridge" },
      { id: "payouts", label: "Payouts & Cash Return" },
    ],
  },
  {
    label: "Analysis",
    sections: [
      { id: "sensitivity_tables", label: "Sensitivity Tables" },
      { id: "scenario_range", label: "Scenario Range" },
      { id: "relative_valuation", label: "Relative Valuation" },
      { id: "reverse_dcf", label: "Reverse DCF" },
      { id: "macro_sensitivity", label: "Macro Sensitivity" },
      { id: "real_options", label: "Real Options" },
    ],
  },
  {
    label: "Research outputs",
    sections: [
      { id: "narrative_to_numbers", label: "Narrative to Numbers" },
      { id: "market_intelligence", label: "Assumption Ledger" },
      { id: "valuation_memo", label: "Valuation Memo" },
    ],
  },
];

const SECTIONS = SECTION_GROUPS.flatMap((group) => group.sections);

function invalidDcfAssumptions(assumptions?: DcfAssumptionSet): string[] {
  if (!assumptions) return [];
  const invalid: string[] = [];
  const bounded: Array<[keyof DcfAssumptionSet, number, number]> = [
    ["current_operating_margin", -1, 1],
    ["target_operating_margin", -1, 1],
    ["tax_rate", 0, 1],
    ["risk_free_rate", 0, 1],
    ["equity_risk_premium", 0, 1],
    ["cost_of_equity", 0, 1],
    ["pre_tax_cost_of_debt", 0, 1],
    ["debt_to_capital", 0, 1],
    ["equity_to_capital", 0, 1],
    ["wacc_start", 0, 1],
    ["wacc_terminal", 0, 1],
    ["terminal_growth_rate", -0.2, 0.2],
    ["terminal_roic", 0, 1],
  ];
  for (const [field, lower, upper] of bounded) {
    const value = assumptions[field];
    if (typeof value === "number" && (value < lower || value > upper)) invalid.push(String(field));
  }
  if (
    typeof assumptions.debt_to_capital === "number"
    && typeof assumptions.equity_to_capital === "number"
    && Math.abs(assumptions.debt_to_capital + assumptions.equity_to_capital - 1) > 0.001
  ) {
    invalid.push("capital structure weights");
  }
  return [...new Set(invalid)];
}

export function AdvancedWorkspace({
  model,
  modelId,
  companyId,
  latestAssumptionSet,
  valuationContext
}: {
  model?: ValuationModel;
  modelId: number;
  companyId: number;
  latestAssumptionSet?: DcfAssumptionSet;
  valuationContext?: ValuationCompanyContext;
}) {
  const [activeSection, setActiveSection] = useState<Section>("setup");
  const [isPending, setIsPending] = useState(false);
  const [reverseDcfPending, setReverseDcfPending] = useState(false);
  const [reverseDcfResponse, setReverseDcfResponse] = useState<ReverseDcfResponse | null>(null);
  const [assumptionNotice, setAssumptionNotice] = useState<string | null>(null);

  const [cashFlowCurrency, setCashFlowCurrency] = useState(valuationContext?.cash_flow_currency || valuationContext?.default_currency || "USD");
  const [discountRateCurrency, setDiscountRateCurrency] = useState(valuationContext?.discount_rate_currency || valuationContext?.default_currency || "USD");
  const [overrideNote, setOverrideNote] = useState("");

  const currencyCheck = buildCurrencyConsistencyCheck({
    companyMarket: valuationContext?.market,
    companyCurrency: valuationContext?.default_currency,
    cashFlowCurrency,
    discountRateCurrency,
    overrideNote
  });

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!currencyCheck.canSave) {
      return;
    }
    setIsPending(true);
    try {
      const formData = new FormData(e.currentTarget);
      const { createDcfAssumptionSet } = await import("@/app/actions");
      await createDcfAssumptionSet(formData, modelId.toString(), companyId.toString());
    } finally {
      setIsPending(false);
    }
  };

  const handleReverseDcfSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!latestAssumptionSet) return;

    setReverseDcfPending(true);
    setReverseDcfResponse(null);
    const formData = new FormData(e.currentTarget);
    const target_parameter = formData.get("target_parameter") as string;
    const current_market_price = parseFloat(formData.get("current_market_price") as string);
    const diluted_shares = parseFloat(formData.get("diluted_shares") as string);

    const { solveReverseDcf } = await import("@/lib/api");
    try {
      const response = await solveReverseDcf({
        assumption_set_id: latestAssumptionSet.id,
        target_parameter,
        current_market_price,
        diluted_shares: isNaN(diluted_shares) ? undefined : diluted_shares
      });
      setReverseDcfResponse(response);
    } catch (err) {
      console.error(err);
    } finally {
      setReverseDcfPending(false);
    }
  };

  const out = latestAssumptionSet?.outputs;
  const warnings = out?.warnings_json || [];
  const diagnosticWarnings: DiagnosticWarning[] = warnings
    .filter((warning) => typeof warning === "object" && warning !== null)
    .map((warning) => ({
      severity: warning.severity,
      module: warning.module,
      message: warning.message,
      affectedAssumptions: warning.affectedAssumptions,
      suggestedFix: warning.suggestedFix ?? undefined,
      formula: warning.formula ?? undefined,
    }));
  const invalidAssumptions = invalidDcfAssumptions(latestAssumptionSet);
  const outputTrustBlocked = invalidAssumptions.length > 0 || diagnosticWarnings.some(
    (warning) => warning.severity === "blocking" || warning.severity === "critical",
  );
  const fallbackScore = Math.max(0, 100 - diagnosticWarnings.reduce((total, warning) => {
    if (warning.severity === "blocking") return total + 35;
    if (warning.severity === "critical") return total + 25;
    if (warning.severity === "warning") return total + 10;
    return total + 5;
  }, 0) - invalidAssumptions.length * 20);
  const score = out?.model_quality_score ?? fallbackScore;
  const outputCurrency = valuationContext?.default_currency || cashFlowCurrency || "USD";
  const hasMarketPrice = typeof out?.current_market_price === "number" && out.current_market_price > 0;
  const hasUpsideComparison = hasMarketPrice && typeof out?.upside_downside_pct === "number";
  const fmt = (n: number | null | undefined, decimals=2) => n != null ? n.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals }) : "—";
  const fmtPct = (n: number | null | undefined) => n != null ? `${(n * 100).toFixed(1)}%` : "—";

  function applyNarrativeAssumptions(updates: Partial<DcfAssumptionSet>) {
    const form = document.getElementById("advanced-dcf-form") as HTMLFormElement | null;
    if (!form) return;
    for (const [name, rawValue] of Object.entries(updates)) {
      const field = form.elements.namedItem(name);
      if (!(field instanceof HTMLInputElement || field instanceof HTMLTextAreaElement)) continue;
      field.value = typeof rawValue === "object" ? JSON.stringify(rawValue) : String(rawValue ?? "");
      field.dispatchEvent(new Event("input", { bubbles: true }));
    }
    setAssumptionNotice("Suggested assumptions were applied to the form. Review them before saving the model.");
  }

  return (
    <div className="valuation-workspace-grid">

      {/* LEFT SIDEBAR (Navigation) */}
      <nav className="valuation-workspace-nav" aria-label="Valuation model sections">
        <label className="valuation-section-select">
          Section
          <select value={activeSection} onChange={(event) => setActiveSection(event.target.value as Section)}>
            {SECTION_GROUPS.map((group) => (
              <optgroup label={group.label} key={group.label}>
                {group.sections.map((section) => <option value={section.id} key={section.id}>{section.label}</option>)}
              </optgroup>
            ))}
          </select>
        </label>
        <div className="valuation-section-groups">
          {SECTION_GROUPS.map((group) => (
            <div className="valuation-section-group" key={group.label}>
              <h3>{group.label}</h3>
              {group.sections.map((section) => (
                <button
                  className={activeSection === section.id ? "is-active" : ""}
                  key={section.id}
                  type="button"
                  onClick={() => setActiveSection(section.id)}
                >
                  {section.label}
                </button>
              ))}
            </div>
          ))}
        </div>
      </nav>

      {/* MAIN CONTENT AREA */}
      <form id="advanced-dcf-form" className="valuation-workspace-main" onSubmit={handleSubmit}>
        <input type="hidden" name="valuation_model_id" value={modelId} />

        <div className="valuation-workspace-main-header">
          <h2>{SECTIONS.find(s => s.id === activeSection)?.label}</h2>
          <button type="submit" disabled={isPending || !currencyCheck.canSave || invalidAssumptions.length > 0} style={{ padding: "0.5rem 1.5rem" }}>
            {isPending ? "Saving..." : "Save & Run Valuation"}
          </button>
        </div>

        {invalidAssumptions.length > 0 ? (
          <div className="valuation-output-blocker" role="alert">
            <strong>Valuation output is blocked by invalid assumption units.</strong>
            <span>Fix: {invalidAssumptions.join(", ")}. Percentages must be stored as decimals.</span>
          </div>
        ) : null}

        {latestAssumptionSet?.is_stale && (
          <div style={{ background: "var(--warning-bg, #fff3cd)", color: "var(--warning-text, #856404)", padding: "1rem", borderRadius: "4px", marginBottom: "2rem", border: "1px solid var(--warning-border, #ffeeba)" }}>
            <strong>Warning: Valuation may be stale.</strong> {latestAssumptionSet.stale_reason}
            <div style={{ marginTop: "0.5rem" }}>
              Check the <strong>Assumption Ledger</strong> tab for proposed adjustments based on recent market events.
            </div>
          </div>
        )}

        <CurrencyConsistencyWarning check={currencyCheck} />

        {/* SECTION CONTENTS */}
        <div style={{ display: activeSection === "setup" ? "block" : "none" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", maxWidth: "500px" }}>
            <SelectField id="scenario" label="Scenario Name" name="scenario" defaultValue={latestAssumptionSet?.scenario || "Base"} required>
              <option value="Base">Base Case</option>
              <option value="Bull">Bull Case</option>
              <option value="Bear">Bear Case</option>
              <option value="Custom">Custom Override</option>
            </SelectField>
            <TextField id="projection_years" label="Projection Years" name="projection_years" type="number" defaultValue={latestAssumptionSet?.projection_years?.length?.toString() || "10"} required />

            <div style={{ borderTop: "1px solid var(--line)", paddingTop: "1.5rem", marginTop: "0.5rem", display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              <h3 style={{ margin: 0, fontSize: "1rem" }}>Currency Settings</h3>
              <TextField id="cash_flow_currency" label="Cash Flow Currency" name="cash_flow_currency" value={cashFlowCurrency} onChange={(e) => setCashFlowCurrency(e.target.value)} required />
              <TextField id="discount_rate_currency" label="Discount Rate / Risk-Free Currency" name="discount_rate_currency" value={discountRateCurrency} onChange={(e) => setDiscountRateCurrency(e.target.value)} required />

              {cashFlowCurrency !== discountRateCurrency && (
                <TextAreaField id="currency_override_note" label="Currency Override Note" name="currency_override_note" placeholder="Explain why discount rate currency differs from cash flows..." value={overrideNote} onChange={(e) => setOverrideNote(e.target.value)} rows={2} required />
              )}
            </div>
          </div>
        </div>

        <div style={{ display: activeSection === "lifecycle" ? "block" : "none" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", maxWidth: "600px" }}>
            {model?.model_type === "distressed" && (
              <div style={{ padding: "1.5rem", border: "1px solid var(--accent)", borderRadius: "8px", background: "var(--accent-light)" }}>
                <h3 style={{ marginTop: 0, marginBottom: "1rem", color: "var(--accent)" }}>Distressed Company Assumptions</h3>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                  <TextField id="probability_of_failure" label="Probability of Failure" name="probability_of_failure" type="number" step="0.01" defaultValue={latestAssumptionSet?.probability_of_failure?.toString() || "0.20"} required />
                  <TextField id="distress_sale_proceeds" label="Distress Sale Proceeds" name="distress_sale_proceeds" type="number" step="0.01" defaultValue={latestAssumptionSet?.distress_sale_proceeds?.toString() || "0"} required />
                </div>
                <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "1rem", marginBottom: 0 }}>
                  Adjusts the Base DCF Value by probability weighting it against failure proceeds.
                </p>
              </div>
            )}

            {model?.model_type === "financial_services" && (
              <div style={{ padding: "1.5rem", border: "1px solid var(--accent)", borderRadius: "8px", background: "var(--accent-light)" }}>
                <h3 style={{ marginTop: 0, marginBottom: "1rem", color: "var(--accent)" }}>Financial Services (Excess Return) Assumptions</h3>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                  <TextField id="book_value_of_equity" label="Book Value of Equity" name="book_value_of_equity" type="number" step="0.01" defaultValue={latestAssumptionSet?.book_value_of_equity?.toString() || "0"} required />
                  <TextField id="target_roe" label="Target ROE" name="target_roe" type="number" step="0.001" defaultValue={latestAssumptionSet?.target_roe?.toString() || "0.10"} required />
                  <TextField id="net_income" label="Starting Net Income" name="net_income" type="number" step="0.01" defaultValue={latestAssumptionSet?.net_income?.toString() || "0"} required />
                </div>
                <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "1rem", marginBottom: 0 }}>
                  Values banks based on Book Equity + Present Value of (ROE - Cost of Equity) * Book Equity.
                </p>
              </div>
            )}

            {model?.model_type !== "distressed" && model?.model_type !== "financial_services" && (
              <div style={{ padding: "1.5rem", border: "1px solid var(--line)", borderRadius: "8px", color: "var(--text-muted)", textAlign: "center" }}>
                No special lifecycle adjustments for a standard ({model?.model_type || "FCFF DCF"}) model.
              </div>
            )}
          </div>
        </div>

        <div style={{ display: activeSection === "story" ? "block" : "none" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
             <TextAreaField id="story_text" label="Company Story" name="story_text" placeholder="What is the overall narrative for this company?" defaultValue={latestAssumptionSet?.story_text || ""} rows={4} />
             <TextAreaField id="growth_story" label="Growth Story" name="growth_story" placeholder="How will they grow revenues?" defaultValue={latestAssumptionSet?.growth_story || ""} rows={3} />
             <TextAreaField id="margin_story" label="Margin Story" name="margin_story" placeholder="What is the path to profitability or maintaining margins?" defaultValue={latestAssumptionSet?.margin_story || ""} rows={3} />
             <TextAreaField id="risk_story" label="Risk Story" name="risk_story" placeholder="What could break this thesis?" defaultValue={latestAssumptionSet?.risk_story || ""} rows={3} />
          </div>
        </div>

        <div style={{ display: activeSection === "market_intelligence" ? "block" : "none" }}>
          {latestAssumptionSet && (
            <ValuationChangeLogPanel modelId={modelId} assumptionSetId={latestAssumptionSet.id} />
          )}
        </div>

        <div style={{ display: activeSection === "revenue" ? "block" : "none" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", maxWidth: "600px" }}>
            <TextField id="starting_revenue" label="Starting Revenue (Base Year)" name="starting_revenue" type="number" step="0.01" defaultValue={latestAssumptionSet?.starting_revenue?.toString()} required />
            <TextAreaField id="revenue_growth_years_json" label="Year-by-Year Revenue Growth (JSON)" name="revenue_growth_years_json" placeholder='{"1": 0.15, "2": 0.12, "3": 0.10}' defaultValue={latestAssumptionSet?.revenue_growth_years_json ? JSON.stringify(latestAssumptionSet.revenue_growth_years_json) : '{"1": 0.10, "2": 0.10, "3": 0.10, "4": 0.10, "5": 0.10}'} rows={4} required />
            <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>Enter explicit growth rates for specific years. Remaining years will interpolate towards the terminal growth rate.</p>
          </div>
        </div>

        <div style={{ display: activeSection === "margins" ? "block" : "none" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem", maxWidth: "500px" }}>
            <h3 style={{ margin: 0 }}>Operating Margins</h3>
            {latestAssumptionSet?.created_at && <DataFreshnessIndicator lastUpdated={new Date(latestAssumptionSet.created_at).toLocaleDateString()} source="Model Assumptions" />}
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", maxWidth: "500px" }}>
            <TextField id="current_operating_margin" label="Current Operating Margin" name="current_operating_margin" type="number" step="0.001" defaultValue={latestAssumptionSet?.current_operating_margin?.toString()} required />
            <TextField id="target_operating_margin" label="Target Operating Margin" name="target_operating_margin" type="number" step="0.001" defaultValue={latestAssumptionSet?.target_operating_margin?.toString()} required />
            <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>Margins will fade linearly from current to target over the projection period.</p>
          </div>
        </div>

        <div style={{ display: activeSection === "reinvestment" ? "block" : "none" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", maxWidth: "500px" }}>
            <TextField id="sales_to_capital_ratio" label="Sales to Capital Ratio" name="sales_to_capital_ratio" type="number" step="0.01" defaultValue={latestAssumptionSet?.sales_to_capital_ratio?.toString() || "1.5"} required />
            <TextField id="starting_invested_capital" label="Starting Invested Capital" name="starting_invested_capital" type="number" step="0.01" defaultValue={latestAssumptionSet?.starting_invested_capital?.toString() || "0"} required />
            <TextField id="tax_rate" label="Effective Tax Rate" name="tax_rate" type="number" step="0.001" defaultValue={latestAssumptionSet?.tax_rate?.toString() || "0.21"} required />
          </div>
        </div>

        <div style={{ display: activeSection === "cost_of_capital" ? "block" : "none" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem", maxWidth: "500px" }}>
            <h3 style={{ margin: 0 }}>Cost of Capital</h3>
            {latestAssumptionSet?.created_at && <DataFreshnessIndicator lastUpdated={new Date(latestAssumptionSet.created_at).toLocaleDateString()} source="Model Assumptions" />}
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", maxWidth: "500px" }}>
            <TextField id="wacc_start" label="Initial WACC (Cost of Capital)" name="wacc_start" type="number" step="0.001" defaultValue={latestAssumptionSet?.wacc_start?.toString()} required />
            <TextField id="wacc_terminal" label="Terminal WACC" name="wacc_terminal" type="number" step="0.001" defaultValue={latestAssumptionSet?.wacc_terminal?.toString()} required />
            <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>WACC will stay constant for half the projection period, then linearly fade to terminal WACC.</p>
          </div>
        </div>

        <div style={{ display: activeSection === "terminal_value" ? "block" : "none" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", maxWidth: "500px" }}>
            <TextField id="terminal_growth_rate" label="Terminal Growth Rate" name="terminal_growth_rate" type="number" step="0.001" defaultValue={latestAssumptionSet?.terminal_growth_rate?.toString()} required />
            <TextField id="terminal_roic" label="Terminal Return on Capital (ROIC)" name="terminal_roic" type="number" step="0.001" defaultValue={latestAssumptionSet?.terminal_roic?.toString()} required />
          </div>
        </div>

        <div style={{ display: activeSection === "payouts" ? "block" : "none" }}>
          <h2>Payouts & Cash Return</h2>
          <p style={{ color: "var(--text-secondary)", marginBottom: "2rem" }}>
            Add Free Cash Flow to Equity (FCFE) and dividend fundamentals. This runs alternative valuation engines alongside the core FCFF model as a cross-check.
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              <h3 style={{ fontSize: "0.9rem", textTransform: "uppercase", color: "var(--text-muted)", margin: 0 }}>Earnings & Cash Flow</h3>
              <TextField id="net_income" label="Net Income ($)" name="net_income" type="number" step="0.01" defaultValue={latestAssumptionSet?.net_income?.toString()} />
              <TextField id="capex" label="Capital Expenditures ($)" name="capex" type="number" step="0.01" defaultValue={latestAssumptionSet?.capex?.toString()} />
              <TextField id="depreciation" label="Depreciation & Amortization ($)" name="depreciation" type="number" step="0.01" defaultValue={latestAssumptionSet?.depreciation?.toString()} />
              <TextField id="change_in_nwc" label="Change in Non-Cash WC ($)" name="change_in_nwc" type="number" step="0.01" defaultValue={latestAssumptionSet?.change_in_nwc?.toString()} />
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              <h3 style={{ fontSize: "0.9rem", textTransform: "uppercase", color: "var(--text-muted)", margin: 0 }}>Payouts & Debt</h3>
              <TextField id="dividends" label="Dividends Paid ($)" name="dividends" type="number" step="0.01" defaultValue={latestAssumptionSet?.dividends?.toString()} />
              <TextField id="buybacks" label="Stock Buybacks ($)" name="buybacks" type="number" step="0.01" defaultValue={latestAssumptionSet?.buybacks?.toString()} />
              <TextField id="stock_issuances" label="Stock Issuances ($)" name="stock_issuances" type="number" step="0.01" defaultValue={latestAssumptionSet?.stock_issuances?.toString()} />
              <TextField id="new_debt_issued" label="New Debt Issued ($)" name="new_debt_issued" type="number" step="0.01" defaultValue={latestAssumptionSet?.new_debt_issued?.toString()} />
              <TextField id="debt_repaid" label="Debt Repaid ($)" name="debt_repaid" type="number" step="0.01" defaultValue={latestAssumptionSet?.debt_repaid?.toString()} />
            </div>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem", marginTop: "2rem" }}>
             <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
                <h3 style={{ fontSize: "0.9rem", textTransform: "uppercase", color: "var(--text-muted)", margin: 0 }}>Demographics (For Expected Yield)</h3>
                <TextField id="company_age" label="Company Age (Years)" name="company_age" type="number" step="0.1" defaultValue={latestAssumptionSet?.company_age?.toString()} />
             </div>
          </div>
        </div>

        <div style={{ display: activeSection === "equity_bridge" ? "block" : "none" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", maxWidth: "500px" }}>
            <TextField id="cash" label="Cash & Equivalents" name="cash" type="number" step="0.01" defaultValue={latestAssumptionSet?.cash?.toString()} required />
            <TextField id="debt" label="Total Debt" name="debt" type="number" step="0.01" defaultValue={latestAssumptionSet?.debt?.toString()} required />
            <TextField id="minority_interests" label="Minority Interests" name="minority_interests" type="number" step="0.01" defaultValue={latestAssumptionSet?.minority_interests?.toString()} />
            <TextField id="preferred_stock" label="Preferred Stock" name="preferred_stock" type="number" step="0.01" defaultValue={latestAssumptionSet?.preferred_stock?.toString() || "0"} />
            <TextField id="employee_options_value" label="Employee Options Value" name="employee_options_value" type="number" step="0.01" defaultValue={latestAssumptionSet?.employee_options_value?.toString() || "0"} />
            <TextField id="diluted_shares" label="Diluted Shares Outstanding" name="diluted_shares" type="number" step="0.01" defaultValue={latestAssumptionSet?.diluted_shares?.toString()} required />
            <TextField id="current_market_price" label="Current Market Price" name="current_market_price" type="number" step="0.01" defaultValue={latestAssumptionSet?.current_market_price?.toString()} required />
          </div>
        </div>

        <div style={{ display: activeSection === "macro_sensitivity" ? "block" : "none" }}>
          {valuationContext ? (
            <MacroSensitivityPanel market={valuationContext.market} country={valuationContext.country} />
          ) : (
            <NotConfiguredState
              title="Market context unavailable"
              description="Set the company market and country before running macro sensitivity."
            />
          )}
        </div>

        <div style={{ display: activeSection === "sensitivity_tables" ? "block" : "none", paddingBottom: "2rem" }}>
          {outputTrustBlocked ? (
            <div className="valuation-output-blocker" role="alert">
              <strong>Sensitivity tables are unavailable for this model.</strong>
              <span>Correct the invalid assumptions and rerun the valuation before using scenario comparisons.</span>
            </div>
          ) : latestAssumptionSet ? (
            <SensitivityTablesPanel
              tables={latestAssumptionSet.sensitivity_tables || []}
              currentMarketPrice={latestAssumptionSet.current_market_price}
              currency={valuationContext?.cash_flow_currency || valuationContext?.default_currency || "USD"}
            />
          ) : null}
        </div>

        <div style={{ display: activeSection === "scenario_range" ? "block" : "none", paddingBottom: "2rem" }}>
          {latestAssumptionSet && (
            <ScenarioRangePanel
              modelId={modelId}
              assumptionId={latestAssumptionSet.id}
              currentMarketPrice={latestAssumptionSet.current_market_price}
            />
          )}
        </div>

        <div style={{ display: activeSection === "relative_valuation" ? "block" : "none" }}>
          <h2 style={{ borderBottom: "1px solid var(--line)", paddingBottom: "1rem", marginBottom: "2rem", marginTop: 0 }}>Relative Valuation</h2>
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

        <div style={{ display: activeSection === "real_options" ? "block" : "none" }}>
          <h2>Real Options Valuation</h2>
          <p style={{ color: "var(--text-secondary)", marginBottom: "2rem" }}>
            Add optionality value to your DCF using the Black-Scholes framework. Only use if the asset meets the eligibility criteria.
          </p>
          <RealOptionsPanel valuationId={modelId.toString()} baseDcfValue={out?.intrinsic_value_per_share || 0} />
        </div>

        <div style={{ display: activeSection === "narrative_to_numbers" ? "block" : "none" }}>
          {latestAssumptionSet && (
            <NarrativeToNumbersPanel
              valuationId={modelId}
              scenario={latestAssumptionSet.scenario}
              currentAssumptions={latestAssumptionSet}
              onApplyAssumptions={applyNarrativeAssumptions}
            />
          )}
          {assumptionNotice ? <p role="status">{assumptionNotice}</p> : null}
        </div>

        <div style={{ display: activeSection === "valuation_memo" ? "block" : "none" }}>
          {latestAssumptionSet && (
            <ValuationMemoPanel
              valuationId={modelId}
              scenario={latestAssumptionSet.scenario}
            />
          )}
        </div>
      </form>

      {/* REVERSE DCF FORM (Overlays Main Area When Active) */}
      <div className="valuation-workspace-main valuation-reverse-dcf" style={{ display: activeSection === "reverse_dcf" ? "block" : "none" }}>
        <h2 style={{ borderBottom: "1px solid var(--line)", paddingBottom: "1rem", marginBottom: "2rem", marginTop: 0 }}>Reverse DCF Engine</h2>
        <p style={{ color: "var(--text-secondary)", marginBottom: "2rem", lineHeight: 1.5 }}>
          Solve for what the market is currently pricing in. Select a parameter and provide the current market price, and the engine will iteratively find the assumption value that justifies the price.
        </p>

        <form onSubmit={handleReverseDcfSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.5rem", maxWidth: "500px", marginBottom: "3rem" }}>
          <SelectField id="target_parameter" label="Parameter to Solve For" name="target_parameter" required>
            <option value="target_operating_margin">Target Operating Margin</option>
            <option value="revenue_growth">Implied Revenue Growth (Flat)</option>
            <option value="wacc_start">Implied WACC</option>
            <option value="terminal_growth_rate">Implied Terminal Growth</option>
          </SelectField>

          <TextField id="reverse_current_market_price" label="Current Market Price ($)" name="current_market_price" type="number" step="0.01" defaultValue={latestAssumptionSet?.current_market_price?.toString() || "100.00"} required />
          <TextField id="reverse_diluted_shares" label="Diluted Shares (Optional Override)" name="diluted_shares" type="number" step="0.01" defaultValue={latestAssumptionSet?.diluted_shares?.toString()} />

          <button type="submit" disabled={reverseDcfPending || !latestAssumptionSet} style={{ padding: "0.75rem", marginTop: "1rem" }}>
            {reverseDcfPending ? "Solving..." : "Solve Reverse DCF"}
          </button>
        </form>

        {reverseDcfResponse && (
          <div style={{ padding: "1.5rem", borderRadius: "8px", background: "var(--bg)", border: "1px solid var(--border-color)" }}>
            <h3 style={{ margin: "0 0 1rem 0" }}>Results</h3>
            <div style={{ display: "flex", gap: "2rem", marginBottom: "1.5rem" }}>
              <div>
                <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>Your Original Assumption</div>
                <div style={{ fontSize: "1.5rem", fontWeight: 600 }}>{fmt(reverseDcfResponse.original_value, 4)}</div>
              </div>
              <div>
                <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>Market Implied Assumption</div>
                <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--accent)" }}>{fmt(reverseDcfResponse.implied_value, 4)}</div>
              </div>
            </div>

            {reverseDcfResponse.diagnostics?.map((w, idx) => (
              <div key={idx} style={{ padding: "1rem", borderRadius: "6px", background: w.severity === "critical" || w.severity === "blocking" ? "rgba(220,38,38,0.1)" : "rgba(245,158,11,0.1)", borderLeft: `4px solid ${w.severity === "critical" || w.severity === "blocking" ? "var(--danger)" : "var(--warning)"}`, marginBottom: "0.5rem" }}>
                <strong>{w.severity.toUpperCase()}</strong>: {w.message}
                {w.suggestedFix && <div style={{ marginTop: "0.5rem", fontSize: "0.85rem" }}><em>Fix:</em> {w.suggestedFix}</div>}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* RIGHT SIDEBAR (Diagnostics & Output Context) */}
      <aside className="valuation-workspace-output">

        {/* Output KPI Card */}
        <div className={`valuation-output-card ${outputTrustBlocked ? "is-blocked" : ""}`}>
          <div style={{ fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", marginBottom: "1rem" }}>Valuation Output</div>
          <div style={{ marginBottom: "1.5rem" }}>
            <div style={{ fontSize: "0.9rem", color: "var(--text-secondary)", display: "flex", alignItems: "center", gap: "0.5rem" }}>
              Intrinsic Value
              <span className="badge" style={{ backgroundColor: "var(--surface-sunken)", padding: "2px 6px", borderRadius: "4px", fontSize: "0.7rem", color: "var(--text-muted)" }}>Estimate</span>
            </div>
            <div className="valuation-output-value">
              {outputTrustBlocked ? "Not reliable" : formatCurrency(out?.intrinsic_value_per_share, outputCurrency)}
            </div>
            {outputTrustBlocked && out?.intrinsic_value_per_share != null ? (
              <div className="valuation-stored-result">Stored calculation: {formatCurrency(out.intrinsic_value_per_share, outputCurrency)}</div>
            ) : null}
            {out?.base_dcf_value != null && (
              <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "0.5rem" }}>
                Base DCF Value: {formatCurrency(out.base_dcf_value, outputCurrency)}
              </div>
            )}
            {out?.pv_of_excess_returns != null && (
              <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "0.5rem" }}>
                PV of Excess Returns: {formatCurrency(out.pv_of_excess_returns, outputCurrency)}
              </div>
            )}
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", paddingBottom: "0.75rem", borderBottom: "1px solid var(--line)", marginBottom: "0.75rem", alignItems: "center" }}>
            <span style={{ color: "var(--text-secondary)", fontSize: "0.9rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
              Current Price
              <span className="badge" style={{ backgroundColor: hasMarketPrice ? "var(--accent-light)" : "var(--surface-sunken)", padding: "2px 6px", borderRadius: "4px", fontSize: "0.7rem", color: hasMarketPrice ? "var(--accent)" : "var(--text-muted)" }}>
                {hasMarketPrice ? "Market Fact" : "Missing data"}
              </span>
            </span>
            <span style={{ fontWeight: 600 }}>{hasMarketPrice ? formatCurrency(out?.current_market_price, outputCurrency) : "Not available"}</span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", paddingBottom: "0.75rem", borderBottom: "1px solid var(--line)", marginBottom: "0.75rem" }}>
            <span style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>Upside</span>
            <span style={{ fontWeight: 600, color: outputTrustBlocked ? "var(--danger)" : out?.upside_downside_pct && out.upside_downside_pct > 0 ? "var(--success)" : "var(--danger)" }}>
              {outputTrustBlocked ? "Not shown" : hasUpsideComparison ? fmtPct(out?.upside_downside_pct) : "Not available"}
            </span>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <span style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>Model Quality</span>
            <span style={{ fontWeight: 600, color: outputTrustBlocked ? "var(--danger)" : score >= 80 ? "var(--success)" : "var(--warning)" }}>{score}/100</span>
          </div>
        </div>

        {/* Relative Pricing Context Card */}
        <div style={{ background: "var(--panel-bg)", padding: "1.5rem", borderRadius: "8px", border: "1px solid var(--border-color)", boxShadow: "0 4px 12px rgba(0,0,0,0.05)" }}>
          <div style={{ fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", marginBottom: "1rem" }}>Relative Pricing Context</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
            <div style={{ display: "flex", flexDirection: "column", paddingBottom: "0.5rem", borderBottom: "1px solid var(--line)" }}>
              <span style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>Implied P/E</span>
              <span style={{ fontWeight: 600 }}>{out?.implied_pe ? `${out.implied_pe.toFixed(1)}x` : "—"}</span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", paddingBottom: "0.5rem", borderBottom: "1px solid var(--line)" }}>
              <span style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>Implied EV/EBITDA</span>
              <span style={{ fontWeight: 600 }}>{out?.implied_ev_ebitda ? `${out.implied_ev_ebitda.toFixed(1)}x` : "—"}</span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", paddingBottom: "0.5rem", borderBottom: "1px solid var(--line)" }}>
              <span style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>Implied EV/Sales</span>
              <span style={{ fontWeight: 600 }}>{out?.implied_ev_sales ? `${out.implied_ev_sales.toFixed(1)}x` : "—"}</span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", paddingBottom: "0.5rem", borderBottom: "1px solid var(--line)" }}>
              <span style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>Implied EV/EBIT</span>
              <span style={{ fontWeight: 600 }}>{out?.implied_ev_ebit ? `${out.implied_ev_ebit.toFixed(1)}x` : "—"}</span>
            </div>
          </div>
          <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "1rem", lineHeight: 1.4 }}>
            These multiples are implied by your DCF assumptions. Compare them to industry averages to see if the market agrees with your growth/margin story.
          </p>
        </div>

        {/* Multi-Method Range Card */}
        <div style={{ background: "var(--panel-bg)", padding: "1.5rem", borderRadius: "8px", border: "1px solid var(--border-color)", boxShadow: "0 4px 12px rgba(0,0,0,0.05)" }}>
          <div style={{ fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", marginBottom: "1rem" }}>Multi-Method Valuation</div>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
             <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
               <span style={{ fontSize: "0.9rem", color: "var(--text-secondary)" }}>FCFF (Core)</span>
               <span style={{ fontWeight: 700 }}>{fmt(out?.intrinsic_value_per_share)}</span>
             </div>
             <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
               <span style={{ fontSize: "0.9rem", color: "var(--text-secondary)" }}>FCFE (Equity)</span>
               <span style={{ fontWeight: 600 }}>{fmt(out?.fcfe_intrinsic_value_per_share)}</span>
             </div>
             <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
               <span style={{ fontSize: "0.9rem", color: "var(--text-secondary)" }}>DDM (Dividends)</span>
               <span style={{ fontWeight: 600 }}>{fmt(out?.ddm_intrinsic_value_per_share)}</span>
             </div>
          </div>
        </div>

        {/* Diagnostics Card */}
        <div style={{ background: "var(--panel-bg)", padding: "1.5rem", borderRadius: "8px", border: "1px solid var(--border-color)", boxShadow: "0 4px 12px rgba(0,0,0,0.05)" }}>
          <div style={{ fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", marginBottom: "1rem" }}>Diagnostics & Warnings</div>
          <DiagnosticPanel warnings={diagnosticWarnings} />
        </div>

      </aside>

    </div>
  );
}
