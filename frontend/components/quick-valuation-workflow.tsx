"use client";

import { useState } from "react";
import {
  postApi,
  type Company,
  type DcfAssumptionSetCreate,
  type QuickValuationAssumptions,
  type QuickValuationOutput,
} from "@/lib/api";
import { SelectField, TextField, TextAreaField } from "@/components/form-fields";
import { Panel } from "@/components/page";

type Step = "select_company" | "edit_assumptions" | "results";

export function QuickValuationWorkflow({ companies }: { companies: Company[] }) {
  const [step, setStep] = useState<Step>("select_company");
  const [selectedCompanyId, setSelectedCompanyId] = useState<number | null>(null);

  // Assumption state
  const [isGenerating, setIsGenerating] = useState(false);
  const [assumptions, setAssumptions] = useState<DcfAssumptionSetCreate>({ scenario: "Quick Run" });
  const [baselineWarnings, setBaselineWarnings] = useState<string[]>([]);

  // Output state
  const [isCalculating, setIsCalculating] = useState(false);
  const [valuationOutput, setValuationOutput] = useState<QuickValuationOutput | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleCompanySelect = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const companyIdStr = formData.get("company_id") as string;
    if (!companyIdStr) return;
    const cid = parseInt(companyIdStr, 10);
    setSelectedCompanyId(cid);

    // Auto-generate assumptions
    setIsGenerating(true);
    setErrorMsg(null);
    try {
      const res = await postApi<QuickValuationAssumptions>(
        "/api/valuation/quick/assumptions",
        { company_id: cid },
      );
      setAssumptions(res.assumptions);
      setBaselineWarnings(res.warnings);
      setStep("edit_assumptions");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown request failure";
      setErrorMsg(`Could not generate baseline assumptions: ${message}`);
      setSelectedCompanyId(null);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRunValuation = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setErrorMsg(null);
    const formData = new FormData(e.currentTarget);

    const parseNum = (name: string, fallback: number = 0) => {
      const val = formData.get(name);
      return val ? parseFloat(val as string) : fallback;
    };

    let growthJson: Record<string, number>;
    try {
      const parsed = JSON.parse(String(formData.get("revenue_growth_years_json") || ""));
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
        throw new Error("Growth input must be a JSON object.");
      }
      growthJson = Object.fromEntries(
        Object.entries(parsed).map(([key, value]) => [key, Number(value)]),
      );
      if (Object.values(growthJson).some((value) => !Number.isFinite(value))) {
        throw new Error("Every growth rate must be numeric.");
      }
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Invalid JSON";
      setErrorMsg(`Revenue growth input is invalid: ${message}`);
      return;
    }

    if (selectedCompanyId === null) {
      setErrorMsg("Select a company before running the valuation.");
      return;
    }
    setIsCalculating(true);

    const payload = {
      company_id: selectedCompanyId,
      starting_revenue: parseNum("starting_revenue"),
      revenue_growth_years_json: growthJson,
      current_operating_margin: parseNum("current_operating_margin"),
      target_operating_margin: parseNum("target_operating_margin"),
      tax_rate: parseNum("tax_rate", 0.21),
      sales_to_capital_ratio: parseNum("sales_to_capital_ratio", 1.5),
      starting_invested_capital: parseNum("starting_invested_capital"),

      wacc_start: parseNum("wacc_start", 0.10),
      wacc_terminal: parseNum("wacc_terminal", 0.08),
      terminal_growth_rate: parseNum("terminal_growth_rate", 0.025),
      terminal_roic: parseNum("terminal_roic", 0.08),

      cash: parseNum("cash"),
      debt: parseNum("debt"),
      minority_interests: parseNum("minority_interests"),
      preferred_stock: parseNum("preferred_stock"),
      employee_options_value: parseNum("employee_options_value"),
      diluted_shares: parseNum("diluted_shares", 1),
      current_market_price: parseNum("current_market_price", 1),

      projection_years_count: 10,
    };

    try {
      const res = await postApi<QuickValuationOutput>("/api/valuation/quick/calculate", payload);
      setValuationOutput(res);
      setStep("results");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown request failure";
      setErrorMsg(`Failed to calculate valuation: ${message}`);
    } finally {
      setIsCalculating(false);
    }
  };

  const resetFlow = () => {
    setStep("select_company");
    setSelectedCompanyId(null);
    setAssumptions({ scenario: "Quick Run" });
    setBaselineWarnings([]);
    setValuationOutput(null);
    setErrorMsg(null);
  };

  const currencyCode = valuationOutput?.currency || companies.find((company) => company.id === selectedCompanyId)?.currency;
  const fmtMoney = (n: number | null | undefined, compact = false) => {
    if (n == null) return "—";
    if (!currencyCode || !/^[A-Z]{3}$/.test(currencyCode)) {
      return `${n.toLocaleString(undefined, { maximumFractionDigits: 2 })} (currency unavailable)`;
    }
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency: currencyCode,
      notation: compact ? "compact" : "standard",
      maximumFractionDigits: 2,
    }).format(n);
  };
  const fmtPct = (n: number | null | undefined) => n != null ? `${(n * 100).toFixed(1)}%` : "—";
  const formDefault = (value: number | null | undefined) => value ?? undefined;
  return (
    <div style={{ maxWidth: "900px", margin: "0 auto", paddingBottom: "4rem" }}>

      {/* Stepper Header */}
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "2rem", borderBottom: "2px solid var(--border-color)", paddingBottom: "1rem" }}>
        <div style={{ fontWeight: step === "select_company" ? 700 : 400, color: step === "select_company" ? "var(--accent)" : "var(--text-muted)" }}>1. Select Company</div>
        <div style={{ fontWeight: step === "edit_assumptions" ? 700 : 400, color: step === "edit_assumptions" ? "var(--accent)" : "var(--text-muted)" }}>2. Review Assumptions</div>
        <div style={{ fontWeight: step === "results" ? 700 : 400, color: step === "results" ? "var(--accent)" : "var(--text-muted)" }}>3. Valuation Output</div>
      </div>

      {errorMsg && (
        <div style={{ padding: "1rem", background: "var(--danger-bg)", color: "var(--danger)", border: "1px solid var(--danger)", borderRadius: "8px", marginBottom: "1.5rem" }}>
          {errorMsg}
        </div>
      )}

      {/* STEP 1: SELECT COMPANY */}
      {step === "select_company" && (
        <Panel title="Which company do you want to value?">
          <form onSubmit={handleCompanySelect} className="form-grid">
            <SelectField id="company_id" name="company_id" label="Company" required>
              <option value="">-- Select a Company --</option>
              {companies.map(c => (
                <option key={c.id} value={c.id}>{c.name} ({c.ticker})</option>
              ))}
            </SelectField>

            <div className="button-row" style={{ marginTop: "1rem" }}>
              <button type="submit" disabled={isGenerating}>
                {isGenerating ? "Generating Baseline..." : "Generate Baseline Assumptions \u2192"}
              </button>
            </div>
          </form>
        </Panel>
      )}

      {/* STEP 2: EDIT ASSUMPTIONS */}
      {step === "edit_assumptions" && (
        <Panel title="Review & Tweak Assumptions">
          <p style={{ color: "var(--text-secondary)", marginBottom: "1.5rem" }}>
            We've generated a baseline set of assumptions. Adjust any inputs you disagree with, then run the valuation.
            These changes and the quick result are not saved.
          </p>
          {baselineWarnings.length > 0 ? (
            <div className="notice notice-warning" style={{ marginBottom: "1.5rem" }}>
              <strong>Baseline requires review.</strong>
              <div style={{ marginTop: "0.35rem" }}>{baselineWarnings.slice(0, 3).join(" ")}</div>
            </div>
          ) : null}
          <form onSubmit={handleRunValuation} className="form-grid">

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2rem" }}>
              {/* Left Column */}
              <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
                <div className="section-block">
                  <h4 style={{ margin: "0 0 1rem 0", color: "var(--accent)" }}>Growth & Margins</h4>
                  <TextField id="starting_revenue" label="Starting Revenue" name="starting_revenue" type="number" step="0.01" defaultValue={formDefault(assumptions.starting_revenue)} required />
                  <TextAreaField id="revenue_growth_years_json" label="Revenue Growth (JSON)" name="revenue_growth_years_json" defaultValue={JSON.stringify(assumptions.revenue_growth_years_json ?? {})} rows={2} required />
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginTop: "1rem" }}>
                    <TextField id="current_operating_margin" label="Current Margin" name="current_operating_margin" type="number" step="0.001" defaultValue={formDefault(assumptions.current_operating_margin)} required />
                    <TextField id="target_operating_margin" label="Target Margin" name="target_operating_margin" type="number" step="0.001" defaultValue={formDefault(assumptions.target_operating_margin)} required />
                  </div>
                </div>

                <div className="section-block">
                  <h4 style={{ margin: "0 0 1rem 0", color: "var(--accent)" }}>Reinvestment</h4>
                  <TextField id="sales_to_capital_ratio" label="Sales to Capital Ratio" name="sales_to_capital_ratio" type="number" step="0.01" defaultValue={formDefault(assumptions.sales_to_capital_ratio)} required />
                  <TextField id="starting_invested_capital" label="Starting Invested Capital" name="starting_invested_capital" type="number" step="0.01" defaultValue={formDefault(assumptions.starting_invested_capital)} required />
                  <TextField id="tax_rate" label="Tax Rate" name="tax_rate" type="number" step="0.001" defaultValue={formDefault(assumptions.tax_rate)} required />
                </div>
              </div>

              {/* Right Column */}
              <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
                <div className="section-block">
                  <h4 style={{ margin: "0 0 1rem 0", color: "var(--accent)" }}>Cost of Capital & Terminal</h4>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                    <TextField id="wacc_start" label="Initial WACC" name="wacc_start" type="number" step="0.001" defaultValue={formDefault(assumptions.wacc_start)} required />
                    <TextField id="wacc_terminal" label="Terminal WACC" name="wacc_terminal" type="number" step="0.001" defaultValue={formDefault(assumptions.wacc_terminal)} required />
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginTop: "1rem" }}>
                    <TextField id="terminal_growth_rate" label="Terminal Growth" name="terminal_growth_rate" type="number" step="0.001" defaultValue={formDefault(assumptions.terminal_growth_rate)} required />
                    <TextField id="terminal_roic" label="Terminal ROIC" name="terminal_roic" type="number" step="0.001" defaultValue={formDefault(assumptions.terminal_roic)} required />
                  </div>
                </div>

                <div className="section-block">
                  <h4 style={{ margin: "0 0 1rem 0", color: "var(--accent)" }}>Bridge to Equity</h4>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                    <TextField id="cash" label="Cash" name="cash" type="number" step="0.01" defaultValue={formDefault(assumptions.cash)} required />
                    <TextField id="debt" label="Debt" name="debt" type="number" step="0.01" defaultValue={formDefault(assumptions.debt)} required />
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginTop: "1rem" }}>
                    <TextField id="diluted_shares" label="Shares Out." name="diluted_shares" type="number" step="0.01" defaultValue={formDefault(assumptions.diluted_shares)} required />
                    <TextField id="current_market_price" label="Market Price" name="current_market_price" type="number" step="0.01" defaultValue={formDefault(assumptions.current_market_price)} required />
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginTop: "1rem" }}>
                    <TextField id="minority_interests" label="Minority Int." name="minority_interests" type="number" step="0.01" defaultValue={assumptions?.minority_interests || 0} />
                    <TextField id="employee_options_value" label="Options Val." name="employee_options_value" type="number" step="0.01" defaultValue={assumptions?.employee_options_value || 0} />
                  </div>
                </div>
              </div>
            </div>

            <div className="button-row" style={{ marginTop: "2rem", display: "flex", justifyContent: "space-between" }}>
              <button type="button" className="secondary-button" onClick={resetFlow}>Cancel</button>
              <button type="submit" disabled={isCalculating} style={{ padding: "0 2rem" }}>
                {isCalculating ? "Calculating..." : "Run Valuation \u2192"}
              </button>
            </div>
          </form>
        </Panel>
      )}

      {/* STEP 3: RESULTS */}
      {step === "results" && valuationOutput && (
        <div style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
          <Panel title="Valuation Results">

            <div className="metric-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", marginBottom: "2rem" }}>
              <div className="metric">
                <div className="metric-label">Intrinsic Value / Share</div>
                <div className="metric-value" style={{ color: "var(--accent)", fontSize: "1.75rem" }}>{fmtMoney(valuationOutput.intrinsic_value_per_share)}</div>
              </div>
              <div className="metric">
                <div className="metric-label">Current Price</div>
                <div className="metric-value">{fmtMoney(valuationOutput.current_market_price)}</div>
              </div>
              <div className="metric">
                <div className="metric-label">Upside / Downside</div>
                <div className="metric-value" style={{ color: valuationOutput.upside_downside_pct && valuationOutput.upside_downside_pct > 0 ? "var(--success)" : "var(--danger)" }}>
                  {fmtPct(valuationOutput.upside_downside_pct)}
                </div>
              </div>
              <div className="metric">
                <div className="metric-label">Equity Value</div>
                <div className="metric-value">{fmtMoney(valuationOutput.equity_value, true)}</div>
              </div>
            </div>

            {valuationOutput.warnings_json && valuationOutput.warnings_json.length > 0 && (
              <div style={{ padding: "1rem", background: "var(--warning-bg)", border: "1px solid var(--warning)", borderRadius: "8px", marginBottom: "2rem" }}>
                <h4 style={{ margin: "0 0 0.5rem 0", color: "var(--warning)" }}>Model Warnings:</h4>
                <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  {valuationOutput.warnings_json.map((w, i) => (
                    <div key={i} style={{ padding: "0.5rem", background: "var(--panel-bg)", borderLeft: `3px solid var(--${w.severity === "critical" || w.severity === "blocking" ? "danger" : "warning"})`, borderRadius: "4px" }}>
                      <strong style={{ color: "var(--text)", display: "block" }}>{w.module.replace("_", " ")}</strong>
                      <span style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>{w.message}</span>
                      {w.suggestedFix && <div style={{ marginTop: "0.5rem", fontSize: "0.85rem", color: "var(--text)" }}><em>Fix: {w.suggestedFix}</em></div>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="notice" style={{ marginBottom: "1.5rem" }}>
              <strong>{valuationOutput.claim_type}</strong> | This quick result is not saved. Use the full valuation workflow for durable scenarios, sensitivity, and reverse DCF.
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", marginTop: "1rem" }}>
              <button type="button" className="secondary-button" onClick={() => setStep("edit_assumptions")}>&larr; Tweak Assumptions</button>
              <button type="button" onClick={resetFlow}>Start New Valuation</button>
            </div>
          </Panel>
        </div>
      )}

    </div>
  );
}
