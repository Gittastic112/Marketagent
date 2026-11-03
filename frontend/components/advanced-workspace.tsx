"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { createRequestGate } from "@/lib/latest-request";
import { useRouter } from "next/navigation";
import type { DcfAssumptionSet, ValuationCompanyContext, ValuationModel } from "@/lib/api/valuation";
import { ReverseDcfPanel } from "@/components/valuation/reverse-dcf-panel";
import { SelectField, TextField, TextAreaField } from "@/components/form-fields";
import { buildCurrencyConsistencyCheck } from "@/lib/valuation-context";
import { CurrencyConsistencyWarning } from "@/components/valuation/currency-consistency-warning";
import { MacroSensitivityPanel } from "@/components/valuation/macro-sensitivity-panel";
import { NarrativeToNumbersPanel } from "@/components/valuation/narrative-to-numbers-panel";
import { ValuationMemoPanel } from "@/components/valuation/valuation-memo-panel";
import { SavedRelativeValuation } from "@/components/valuation/saved-relative-valuation";
import { ImpliedPricingPanel } from "@/components/valuation/implied-pricing-panel";
import { SensitivityTablesPanel } from "@/components/valuation/sensitivity-tables-panel";
import { ScenarioRangePanel } from "@/components/valuation/scenario-range-panel";
import { RealOptionsPanel } from "@/components/valuation/real-options-panel";
import { ValuationChangeLogPanel } from "@/components/valuation/valuation-change-log-panel";
import { DiagnosticPanel, DiagnosticWarning } from "@/components/valuation/diagnostic-panel";
import { NotConfiguredState, DataFreshnessIndicator } from "@/components/ui/data-states";
import { buildValuationOutputState, invalidDcfAssumptions } from "@/lib/valuation-output-state";
import { SavedValuationOutputCard, MultiMethodValuationCard } from "@/components/valuation/saved-output-cards";
import { SavedProjections } from "@/components/valuation/saved-projections";

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
  const router = useRouter();
  const [activeSection, setActiveSection] = useState<Section>("setup");
  const [isPending, setIsPending] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);
  const [assumptionNotice, setAssumptionNotice] = useState<string | null>(null);
  const saves = useMemo(createRequestGate, [modelId]);
  const saving = useRef(false);
  useEffect(() => () => saves.invalidate(), [saves]);

  const [cashFlowCurrency, setCashFlowCurrency] = useState(latestAssumptionSet ? latestAssumptionSet.cash_flow_currency ?? "" : valuationContext?.cash_flow_currency || valuationContext?.default_currency || "USD");
  const [discountRateCurrency, setDiscountRateCurrency] = useState(latestAssumptionSet ? latestAssumptionSet.discount_rate_currency ?? "" : valuationContext?.discount_rate_currency || valuationContext?.default_currency || "USD");
  const [overrideNote, setOverrideNote] = useState(latestAssumptionSet?.currency_override_note || "");

  useEffect(() => {
    setCashFlowCurrency(latestAssumptionSet ? latestAssumptionSet.cash_flow_currency ?? "" : valuationContext?.cash_flow_currency || valuationContext?.default_currency || "USD");
    setDiscountRateCurrency(latestAssumptionSet ? latestAssumptionSet.discount_rate_currency ?? "" : valuationContext?.discount_rate_currency || valuationContext?.default_currency || "USD");
    setOverrideNote(latestAssumptionSet?.currency_override_note || "");
    setAssumptionNotice(null);
  }, [latestAssumptionSet, valuationContext]);

  const currencyCheck = buildCurrencyConsistencyCheck({
    companyMarket: valuationContext?.market,
    companyCurrency: valuationContext?.default_currency,
    cashFlowCurrency,
    discountRateCurrency,
    overrideNote
  });

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (saving.current) return;
    if (!valuationContext || !currencyCheck.canSave) {
      return;
    }
    setSaveError(null);
    setSaveSuccess(null);
    // Required controls can live in another section. Reveal the first invalid
    // control instead of letting native validation fail on a hidden element.
    const invalid = Array.from(e.currentTarget.elements).find(element =>
      (element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement || element instanceof HTMLSelectElement)
      && !element.disabled && !element.validity.valid) as HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement | undefined;
    if (invalid) {
      const section = invalid.closest<HTMLElement>("[data-valuation-section]")?.dataset.valuationSection;
      if (section) setActiveSection(section as Section);
      setSaveError(`${invalid.labels?.[0]?.textContent ?? invalid.name}: ${invalid.validationMessage}`);
      requestAnimationFrame(() => invalid.focus());
      return;
    }
    const current = saves.begin();
    saving.current = true;
    setIsPending(true);
    try {
      const formData = new FormData(e.currentTarget);
      if (latestAssumptionSet) {
        formData.set("base_assumption_set_id", String(latestAssumptionSet.id));
        formData.set("base_assumption_set_updated_at", latestAssumptionSet.updated_at);
      }
      const { createDcfAssumptionSetWithState } = await import("@/app/actions");
      const result = await createDcfAssumptionSetWithState(formData, modelId.toString(), companyId.toString());
      if (!current()) return;
      if (result.error) {
        setSaveError(result.error);
        return;
      }
      setSaveSuccess("Assumptions saved and valuation recalculated.");
      router.refresh();
    } catch (error) {
      if (current()) setSaveError(error instanceof Error ? error.message : "Could not save and calculate the valuation.");
    } finally {
      saving.current = false;
      if (current()) setIsPending(false);
    }
  };


  const out = latestAssumptionSet?.outputs;
  const isEquityModel = model?.model_type === "financial_services";
  const outputState = buildValuationOutputState(latestAssumptionSet, model?.model_type);
  const diagnosticWarnings = outputState.diagnosticWarnings.map(warning => ({ ...warning,
    suggestedFix: warning.suggestedFix ?? undefined, formula: warning.formula ?? undefined }));
  const invalidAssumptions = invalidDcfAssumptions(latestAssumptionSet, model?.model_type);
  const outputTrustBlocked = outputState.blocked;
  const savedNumber = (field: keyof DcfAssumptionSet, initial: string = "") => {
    const value = latestAssumptionSet?.[field];
    return typeof value === "number" ? String(value) : latestAssumptionSet ? "" : initial;
  };

  function applyNarrativeAssumptions(updates: Partial<DcfAssumptionSet>) {
    const form = document.getElementById("advanced-dcf-form") as HTMLFormElement | null;
    if (!form) return;
    for (const [name, rawValue] of Object.entries(updates)) {
      const field = form.elements.namedItem(name);
      if (!(field instanceof HTMLInputElement || field instanceof HTMLTextAreaElement)) continue;
      field.value = typeof rawValue === "object" ? JSON.stringify(rawValue) : String(rawValue ?? "");
      field.dispatchEvent(new Event("input", { bubbles: true }));
    }
    setSaveSuccess(null);
    setAssumptionNotice("Reviewed AI estimates were copied to unsaved fields. Inspect them and use Save & Run Valuation to create a new version. The saved model is unchanged.");
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
      <form key={latestAssumptionSet?.id ?? "new"} id="advanced-dcf-form" className="valuation-workspace-main" onSubmit={handleSubmit} noValidate
        onChange={() => setSaveSuccess(null)}
        style={{ display: activeSection === "real_options" || activeSection === "reverse_dcf" ? "none" : undefined }}>
        <fieldset disabled={isPending} style={{display: "contents"}}>
        <legend className="sr-only">Saved valuation inputs and analysis</legend>
        <input type="hidden" name="valuation_model_id" value={modelId} />
        <input type="hidden" name="reinvestment_method" value={latestAssumptionSet?.reinvestment_method || "sales_to_capital"} />

        <div className="valuation-workspace-main-header">
          <h2>{SECTIONS.find(s => s.id === activeSection)?.label}</h2>
          <button type="submit" disabled={isPending || !valuationContext || !currencyCheck.canSave} style={{ padding: "0.5rem 1.5rem" }}>
            {isPending ? "Saving..." : "Save & Run Valuation"}
          </button>
        </div>

        {saveError ? <div className="inline-error" role="alert">{saveError}</div> : null}
        {saveSuccess ? <p role="status" style={{ color: "var(--success)", fontWeight: 600 }}>{saveSuccess}</p> : null}
        <p className="notice" style={{ marginTop: 0 }}>
          <strong>User Assumption</strong> inputs are versioned on save. Valuation outputs are deterministic <strong>Calculations</strong> and per-share values are <strong>Estimates</strong>, not recommendations.
        </p>
        {!valuationContext ? (
          <div className="valuation-output-blocker" role="alert">
            <strong>Saving is blocked because market context is unavailable.</strong>
            <span>Restore the backend context response and verify company market, country, and currency first.</span>
          </div>
        ) : null}

        {invalidAssumptions.length > 0 ? (
          <div className="valuation-output-blocker" role="alert">
            <strong>Valuation output is blocked by invalid assumption units.</strong>
            <span>Fix: {invalidAssumptions.join(", ")}. Percentages must be stored as decimals. Correct the form and save a new calculation; the backend validates the submitted values.</span>
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
        <div data-valuation-section="setup" style={{ display: activeSection === "setup" ? "block" : "none" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", maxWidth: "500px" }}>
            <SelectField id="scenario" label="Scenario Name" name="scenario" defaultValue={latestAssumptionSet?.scenario || "Base"} required>
              <option value="Base">Base Case</option>
              <option value="Bull">Bull Case</option>
              <option value="Bear">Bear Case</option>
              <option value="Custom">Custom Override</option>
            </SelectField>
            <TextField id="projection_years" label="Projection Years" name="projection_years" type="number" min="1" max="30" defaultValue={savedNumber("projection_years_count", "10")} required />

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

        <div data-valuation-section="lifecycle" style={{ display: activeSection === "lifecycle" ? "block" : "none" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", maxWidth: "600px" }}>
            {model?.model_type === "distressed" && (
              <div style={{ padding: "1.5rem", border: "1px solid var(--accent)", borderRadius: "8px", background: "var(--accent-light)" }}>
                <h3 style={{ marginTop: 0, marginBottom: "1rem", color: "var(--accent)" }}>Distressed Company Assumptions</h3>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                  <TextField id="probability_of_failure" label="Probability of Failure (decimal, 0 to 1)" name="probability_of_failure" type="number" min="0" max="1" step="any" defaultValue={savedNumber("probability_of_failure")} required />
                  <TextField id="distress_sale_proceeds" label={`Common-equity recovery on failure (${cashFlowCurrency}, total)`} name="distress_sale_proceeds" type="number" min="0" step="any" defaultValue={savedNumber("distress_sale_proceeds")} required />
                </div>
                <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "1rem", marginBottom: 0 }}>
                  Enter explicit User Assumptions, including zero when intended. Recovery means the total amount left for common equity after senior claims, not enterprise sale proceeds or a per-share amount. Use the same currency and monetary scale as the saved equity value. No independent recovery verification is implied.
                </p>
              </div>
            )}

            {model?.model_type === "financial_services" && (
              <div style={{ padding: "1.5rem", border: "1px solid var(--accent)", borderRadius: "8px", background: "var(--accent-light)" }}>
                <h3 style={{ marginTop: 0, marginBottom: "1rem", color: "var(--accent)" }}>Financial Services (Excess Return) Assumptions</h3>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                  <TextField id="target_roe" label="Target ROE (decimal)" name="target_roe" type="number" min="-1" max="1" step="any" defaultValue={savedNumber("target_roe")} required />
                </div>
                <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "1rem", marginBottom: 0 }}>
                  Values banks based on book equity plus discounted excess returns. Review book equity and net income under Payouts & Cash Return, cost of equity under Cost of Capital, and growth under Terminal Value. The model uses constant book-equity growth and linear ROE fade, not a regulatory-capital or payout forecast. Operating-company fields are optional and are not used by this engine.
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
             <TextAreaField id="reinvestment_story" label="Reinvestment Story" name="reinvestment_story" placeholder="What reinvestment is required to support the growth path?" defaultValue={latestAssumptionSet?.reinvestment_story || ""} rows={3} />
             <TextAreaField id="risk_story" label="Risk Story" name="risk_story" placeholder="What could break this thesis?" defaultValue={latestAssumptionSet?.risk_story || ""} rows={3} />
          </div>
        </div>

        <div style={{ display: activeSection === "market_intelligence" ? "block" : "none" }}>
          {latestAssumptionSet ? (
            <ValuationChangeLogPanel modelId={modelId} assumptionSetId={latestAssumptionSet.id} />
          ) : <NotConfiguredState title="Assumption ledger unavailable" description="Save the first reviewed assumption set to start the change ledger." />}
        </div>

        <div data-valuation-section="revenue" style={{ display: activeSection === "revenue" ? "block" : "none" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", maxWidth: "600px" }}>
            <TextField id="starting_revenue" label="Starting Revenue (Base Year)" name="starting_revenue" type="number" step="0.01" defaultValue={latestAssumptionSet?.starting_revenue?.toString()} required={!isEquityModel} />
            <TextAreaField id="revenue_growth_years_json" label="Year-by-Year Revenue Growth (JSON)" name="revenue_growth_years_json" placeholder='{"1": 0.15, "2": 0.12, "3": 0.10}' defaultValue={latestAssumptionSet?.revenue_growth_years_json ? JSON.stringify(latestAssumptionSet.revenue_growth_years_json) : ""} rows={4} required={!isEquityModel} />
            <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>Enter explicit decimal growth rates for each projection year. The current engine uses zero growth for omitted years; it does not interpolate them.</p>
          </div>
        </div>

        <div data-valuation-section="margins" style={{ display: activeSection === "margins" ? "block" : "none" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem", maxWidth: "500px" }}>
            <h3 style={{ margin: 0 }}>Operating Margins</h3>
            {latestAssumptionSet?.created_at && <DataFreshnessIndicator lastUpdated={new Date(latestAssumptionSet.created_at).toLocaleDateString()} source="Model Assumptions" />}
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", maxWidth: "500px" }}>
            <TextField id="current_operating_margin" label="Current Operating Margin" name="current_operating_margin" type="number" step="0.001" defaultValue={latestAssumptionSet?.current_operating_margin?.toString()} required={!isEquityModel} />
            <TextField id="target_operating_margin" label="Target Operating Margin" name="target_operating_margin" type="number" step="0.001" defaultValue={latestAssumptionSet?.target_operating_margin?.toString()} required={!isEquityModel} />
            <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>Margins will fade linearly from current to target over the projection period.</p>
          </div>
        </div>

        <div data-valuation-section="reinvestment" style={{ display: activeSection === "reinvestment" ? "block" : "none" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", maxWidth: "500px" }}>
            <TextField id="sales_to_capital_ratio" label="Sales to Capital Ratio" name="sales_to_capital_ratio" type="number" step="0.01" defaultValue={savedNumber("sales_to_capital_ratio")} required={!isEquityModel} />
            <TextField id="starting_invested_capital" label="Starting Invested Capital" name="starting_invested_capital" type="number" step="0.01" defaultValue={savedNumber("starting_invested_capital")} required={!isEquityModel} />
            <TextField id="tax_rate" label="Effective Tax Rate" name="tax_rate" type="number" step="0.001" defaultValue={savedNumber("tax_rate")} required={!isEquityModel} />
          </div>
        </div>

        <div data-valuation-section="cost_of_capital" style={{ display: activeSection === "cost_of_capital" ? "block" : "none" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem", maxWidth: "500px" }}>
            <h3 style={{ margin: 0 }}>Cost of Capital</h3>
            {latestAssumptionSet?.created_at && <DataFreshnessIndicator lastUpdated={new Date(latestAssumptionSet.created_at).toLocaleDateString()} source="Model Assumptions" />}
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", maxWidth: "500px" }}>
            <TextField id="risk_free_rate" label="Risk-Free Rate" name="risk_free_rate" type="number" step="0.001" defaultValue={latestAssumptionSet?.risk_free_rate?.toString()} />
            <TextField id="equity_risk_premium" label="Equity Risk Premium" name="equity_risk_premium" type="number" step="0.001" defaultValue={latestAssumptionSet?.equity_risk_premium?.toString()} />
            <TextField id="beta" label="Beta" name="beta" type="number" step="0.01" defaultValue={latestAssumptionSet?.beta?.toString()} />
            <TextField id="cost_of_equity" label="Cost of Equity" name="cost_of_equity" type="number" min="0" max="1" step="any" defaultValue={latestAssumptionSet?.cost_of_equity?.toString()} required={isEquityModel} />
            <TextField id="pre_tax_cost_of_debt" label="Pre-Tax Cost of Debt" name="pre_tax_cost_of_debt" type="number" step="0.001" defaultValue={latestAssumptionSet?.pre_tax_cost_of_debt?.toString()} />
            <TextField id="debt_to_capital" label="Debt to Capital" name="debt_to_capital" type="number" step="0.001" defaultValue={latestAssumptionSet?.debt_to_capital?.toString()} />
            <TextField id="equity_to_capital" label="Equity to Capital" name="equity_to_capital" type="number" step="0.001" defaultValue={latestAssumptionSet?.equity_to_capital?.toString()} />
            <TextField id="wacc_start" label="Initial WACC (Cost of Capital)" name="wacc_start" type="number" step="0.001" defaultValue={latestAssumptionSet?.wacc_start?.toString()} required={!isEquityModel} />
            <TextField id="wacc_terminal" label="Terminal WACC" name="wacc_terminal" type="number" step="0.001" defaultValue={latestAssumptionSet?.wacc_terminal?.toString()} required={!isEquityModel} />
            <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>WACC will stay constant for half the projection period, then linearly fade to terminal WACC.</p>
          </div>
        </div>

        <div data-valuation-section="terminal_value" style={{ display: activeSection === "terminal_value" ? "block" : "none" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", maxWidth: "500px" }}>
            <TextField id="terminal_growth_rate" label={isEquityModel ? "Book Equity Growth (decimal, forecast and terminal)" : "Terminal Growth Rate"} name="terminal_growth_rate" type="number" step="0.001" defaultValue={latestAssumptionSet?.terminal_growth_rate?.toString()} required />
            <TextField id="terminal_roic" label="Terminal Return on Capital (ROIC)" name="terminal_roic" type="number" step="0.001" defaultValue={latestAssumptionSet?.terminal_roic?.toString()} required={!isEquityModel} />
          </div>
        </div>

        <div data-valuation-section="payouts" style={{ display: activeSection === "payouts" ? "block" : "none" }}>
          <h2>Payouts & Cash Return</h2>
          <p style={{ color: "var(--text-secondary)", marginBottom: "2rem" }}>
            {isEquityModel
              ? "Book equity and net income are required for the excess-return model. Optional cash-flow and payout fields are retained for context, not used to calculate this bank model."
              : model?.model_type === "distressed"
                ? "Cash-flow and payout inputs are retained for context. Unadjusted FCFE/DDM estimates are not displayed as probability-weighted distressed values."
                : "Add Free Cash Flow to Equity (FCFE) and dividend fundamentals. Complete explicit inputs allow single-stage estimates alongside the core FCFF model as a cross-check."}
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              <h3 style={{ fontSize: "0.9rem", textTransform: "uppercase", color: "var(--text-muted)", margin: 0 }}>Earnings & Cash Flow</h3>
              <TextField id="book_value_of_equity" label={`Book Value of Equity (${cashFlowCurrency})`} name="book_value_of_equity" type="number" step="0.01" defaultValue={latestAssumptionSet?.book_value_of_equity?.toString() ?? ""} required={model?.model_type === "financial_services"} />
              <TextField id="net_income" label={`Net Income (${cashFlowCurrency})`} name="net_income" type="number" step="0.01" defaultValue={latestAssumptionSet?.net_income?.toString()} required={isEquityModel} />
              <TextField id="capex" label={`Capital Expenditures (${cashFlowCurrency})`} name="capex" type="number" step="0.01" defaultValue={latestAssumptionSet?.capex?.toString()} />
              <TextField id="depreciation" label={`Depreciation (${cashFlowCurrency}; verify amortization separately)`} name="depreciation" type="number" step="0.01" defaultValue={latestAssumptionSet?.depreciation?.toString()} />
              <TextField id="change_in_nwc" label={`Change in Non-Cash WC (${cashFlowCurrency})`} name="change_in_nwc" type="number" step="0.01" defaultValue={latestAssumptionSet?.change_in_nwc?.toString()} />
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
              <h3 style={{ fontSize: "0.9rem", textTransform: "uppercase", color: "var(--text-muted)", margin: 0 }}>Payouts & Debt</h3>
              <TextField id="dividends" label={`Dividends Paid (${cashFlowCurrency})`} name="dividends" type="number" step="0.01" defaultValue={latestAssumptionSet?.dividends?.toString()} />
              <TextField id="buybacks" label={`Stock Buybacks (${cashFlowCurrency})`} name="buybacks" type="number" step="0.01" defaultValue={latestAssumptionSet?.buybacks?.toString()} />
              <TextField id="stock_issuances" label={`Stock Issuances (${cashFlowCurrency})`} name="stock_issuances" type="number" step="0.01" defaultValue={latestAssumptionSet?.stock_issuances?.toString()} />
              <TextField id="new_debt_issued" label={`New Debt Issued (${cashFlowCurrency})`} name="new_debt_issued" type="number" step="0.01" defaultValue={latestAssumptionSet?.new_debt_issued?.toString()} />
              <TextField id="debt_repaid" label={`Debt Repaid (${cashFlowCurrency})`} name="debt_repaid" type="number" step="0.01" defaultValue={latestAssumptionSet?.debt_repaid?.toString()} />
            </div>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem", marginTop: "2rem" }}>
             <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
                <h3 style={{ fontSize: "0.9rem", textTransform: "uppercase", color: "var(--text-muted)", margin: 0 }}>Demographics (For Expected Yield)</h3>
                <TextField id="company_age" label="Company Age (Years)" name="company_age" type="number" step="0.1" defaultValue={latestAssumptionSet?.company_age?.toString()} />
             </div>
          </div>
        </div>

        <div data-valuation-section="equity_bridge" style={{ display: activeSection === "equity_bridge" ? "block" : "none" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", maxWidth: "500px" }}>
            <TextField id="cash" label="Cash & Equivalents" name="cash" type="number" step="0.01" defaultValue={latestAssumptionSet?.cash?.toString()} required={!isEquityModel} />
            <TextField id="cross_holdings" label="Cross Holdings" name="cross_holdings" type="number" step="0.01" defaultValue={latestAssumptionSet?.cross_holdings?.toString()} />
            <TextField id="debt" label="Total Debt" name="debt" type="number" step="0.01" defaultValue={latestAssumptionSet?.debt?.toString()} required={!isEquityModel} />
            <TextField id="operating_leases" label="Operating Leases" name="operating_leases" type="number" step="0.01" defaultValue={latestAssumptionSet?.operating_leases?.toString()} />
            <TextField id="minority_interests" label="Minority Interests" name="minority_interests" type="number" step="0.01" defaultValue={latestAssumptionSet?.minority_interests?.toString()} />
            <TextField id="preferred_stock" label="Preferred Stock" name="preferred_stock" type="number" step="0.01" defaultValue={savedNumber("preferred_stock")} />
            <TextField id="employee_options_value" label="Employee Options Value" name="employee_options_value" type="number" step="0.01" defaultValue={savedNumber("employee_options_value")} />
            <TextField id="diluted_shares" label="Diluted Shares Outstanding" name="diluted_shares" type="number" step="0.01" defaultValue={latestAssumptionSet?.diluted_shares?.toString()} required />
            <TextField id="basic_shares" label="Basic Shares Outstanding" name="basic_shares" type="number" step="0.01" defaultValue={latestAssumptionSet?.basic_shares?.toString()} />
            <TextField id="current_market_price" label={`Comparison Price (${cashFlowCurrency}, User Assumption, optional)`} name="current_market_price" type="number" min="0.000001" step="any" defaultValue={latestAssumptionSet?.current_market_price?.toString()} />
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
              currency={latestAssumptionSet.cash_flow_currency || valuationContext?.cash_flow_currency || valuationContext?.default_currency || "USD"}
            />
          ) : <NotConfiguredState title="Sensitivity tables unavailable" description="Save and run the first valid assumption set to generate deterministic sensitivity tables." />}
        </div>

        <div style={{ display: activeSection === "scenario_range" ? "block" : "none", paddingBottom: "2rem" }}>
          {latestAssumptionSet && <SavedProjections assumptions={latestAssumptionSet} modelType={model?.model_type} />}
          {latestAssumptionSet && activeSection === "scenario_range" && !outputTrustBlocked ? (
            <ScenarioRangePanel modelId={modelId} assumptions={latestAssumptionSet} modelType={model?.model_type} />
          ) : <NotConfiguredState title="Scenario range unavailable" description="Review the saved output blockers and save a valid calculation before generating scenario ranges." />}
        </div>

        <div style={{ display: activeSection === "relative_valuation" ? "block" : "none" }}>
          <h2 style={{ borderBottom: "1px solid var(--line)", paddingBottom: "1rem", marginBottom: "2rem", marginTop: 0 }}>Relative Valuation</h2>
          {latestAssumptionSet && activeSection === "relative_valuation" ? <SavedRelativeValuation
            assumptionId={latestAssumptionSet.id}
          /> : !latestAssumptionSet ? <NotConfiguredState title="Relative valuation inputs unavailable" description="Save the first assumption set before applying benchmark multiples." /> : null}
        </div>

        <div style={{ display: activeSection === "narrative_to_numbers" ? "block" : "none" }}>
          {latestAssumptionSet ? (
            <NarrativeToNumbersPanel
              key={`${latestAssumptionSet.id}:${latestAssumptionSet.updated_at}`}
              valuationId={modelId}
              scenario={latestAssumptionSet.scenario}
              currentAssumptions={latestAssumptionSet}
              onApplyAssumptions={applyNarrativeAssumptions}
            />
          ) : <NotConfiguredState title="Narrative mapping unavailable" description="Save the first assumption set before mapping narrative changes into model inputs." />}
          {assumptionNotice ? <p role="status">{assumptionNotice}</p> : null}
        </div>

        <div style={{ display: activeSection === "valuation_memo" ? "block" : "none" }}>
          {latestAssumptionSet ? (
            <ValuationMemoPanel
              key={`${latestAssumptionSet.id}:${latestAssumptionSet.updated_at}`}
              valuationId={modelId}
              assumptions={latestAssumptionSet}
              blocked={outputTrustBlocked || Boolean(latestAssumptionSet.is_stale)}
            />
          ) : <NotConfiguredState title="Valuation memo unavailable" description="Save and calculate the first assumption set before generating a memo." />}
        </div>
        </fieldset>
      </form>

      <div className="valuation-workspace-main valuation-standalone-analysis" style={{ display: activeSection === "real_options" ? "block" : "none" }}>
        {activeSection === "real_options" && latestAssumptionSet ? (
          <RealOptionsPanel key={`${latestAssumptionSet.id}:${latestAssumptionSet.updated_at}:${model?.model_type}`}
            assumptions={latestAssumptionSet} modelType={model?.model_type ?? "fcff_dcf"} />
        ) : activeSection === "real_options" ? <NotConfiguredState title="Real Options unavailable" description="Save and calculate reviewed assumptions first." /> : null}
      </div>

      <div className="valuation-workspace-main valuation-standalone-analysis" style={{ display: activeSection === "reverse_dcf" ? "block" : "none" }}>
        {activeSection === "reverse_dcf" && latestAssumptionSet ? (
          <ReverseDcfPanel key={`${latestAssumptionSet.id}:${latestAssumptionSet.updated_at}:${model?.model_type}`}
            assumptions={latestAssumptionSet} modelType={model?.model_type ?? "fcff_dcf"} />
        ) : activeSection === "reverse_dcf" ? <NotConfiguredState title="Reverse DCF unavailable" description="Save and calculate reviewed assumptions first." /> : null}
      </div>

      {/* RIGHT SIDEBAR (Diagnostics & Output Context) */}
      <aside className="valuation-workspace-output">

        <SavedValuationOutputCard state={outputState} />

        <ImpliedPricingPanel basis={out?.implied_pricing_basis}
          blocked={outputTrustBlocked || Boolean(latestAssumptionSet?.is_stale)} />

        <MultiMethodValuationCard state={outputState} modelType={model?.model_type} />

        {/* Diagnostics Card */}
        <div style={{ background: "var(--panel-bg)", padding: "1.5rem", borderRadius: "8px", border: "1px solid var(--border-color)", boxShadow: "0 4px 12px rgba(0,0,0,0.05)" }}>
          <div style={{ fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--text-muted)", marginBottom: "1rem" }}>Diagnostics & Warnings</div>
          {out ? <DiagnosticPanel warnings={diagnosticWarnings} /> : <p>No saved diagnostics. Save and calculate a model first.</p>}
        </div>

      </aside>

    </div>
  );
}
