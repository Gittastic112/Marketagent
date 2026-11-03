import type { DcfAssumptionSet, DcfOutput, DiagnosticWarning } from "./api.ts";

type SavedAssumptions = Omit<Partial<DcfAssumptionSet>, "outputs">;
type SavedOutputContext = SavedAssumptions & {
  outputs?: (Omit<Partial<DcfOutput>, "warnings_json"> & { warnings_json?: unknown }) | null;
};

export const finiteOutput = (value: unknown): value is number => typeof value === "number" && Number.isFinite(value);

export function invalidDcfAssumptions(assumptions?: SavedAssumptions, modelType = "fcff_dcf"): string[] {
  if (!assumptions) return [];
  const invalid: string[] = [];
  if (modelType === "financial_services") {
    for (const [field, low, high] of [
      ["book_value_of_equity", 0, Infinity], ["diluted_shares", 0, Infinity],
      ["net_income", -Infinity, Infinity], ["target_roe", -1, 1],
      ["cost_of_equity", 0, 1], ["terminal_growth_rate", -.2, .2],
    ] as const) {
      const value = assumptions[field];
      if (!finiteOutput(value) || value < low || value > high
          || (["book_value_of_equity", "diluted_shares"].includes(field) && value === 0)) invalid.push(field);
    }
    return invalid;
  }
  const bounded: Array<[keyof SavedAssumptions, number, number]> = [
    ["current_operating_margin", -1, 1], ["target_operating_margin", -1, 1],
    ["tax_rate", 0, 1], ["risk_free_rate", 0, 1], ["equity_risk_premium", 0, 1],
    ["cost_of_equity", 0, 1], ["pre_tax_cost_of_debt", 0, 1],
    ["debt_to_capital", 0, 1], ["equity_to_capital", 0, 1],
    ["wacc_start", 0, 1], ["wacc_terminal", 0, 1],
    ["terminal_growth_rate", -0.2, 0.2], ["terminal_roic", 0, 1], ["beta", 0, 5],
    ["probability_of_failure", 0, 1], ["target_roe", -1, 1],
  ];
  for (const [key, low, high] of bounded) {
    const value = assumptions[key];
    if (value != null && (!finiteOutput(value) || value < low || value > high)) invalid.push(key);
  }
  for (const key of ["starting_revenue", "sales_to_capital_ratio", "starting_invested_capital", "diluted_shares"] as const) {
    const value = assumptions[key];
    if (value != null && (!finiteOutput(value) || value <= 0)) invalid.push(key);
  }
  if (finiteOutput(assumptions.debt_to_capital) && finiteOutput(assumptions.equity_to_capital)
      && Math.abs(assumptions.debt_to_capital + assumptions.equity_to_capital - 1) > 0.001) invalid.push("capital structure weights");
  return invalid;
}

function diagnostics(value: unknown): DiagnosticWarning[] {
  const review: DiagnosticWarning = { severity: "blocking", module: "diagnostic_review",
    message: "Stored diagnostic status is missing or unrecognized. Review and rerun this model.", affectedAssumptions: [], suggestedFix: null, formula: null };
  if (!Array.isArray(value)) return [review];
  return value.map(item => {
    if (!item || typeof item !== "object" || !["info", "watch", "warning", "critical", "blocking"].includes(item.severity)
        || typeof item.module !== "string" || typeof item.message !== "string") return review;
    return { severity: item.severity, module: item.module, message: item.message,
      affectedAssumptions: Array.isArray(item.affectedAssumptions) ? item.affectedAssumptions.filter((v: unknown) => typeof v === "string") : [],
      suggestedFix: typeof item.suggestedFix === "string" ? item.suggestedFix : null,
      formula: typeof item.formula === "string" ? item.formula : null };
  });
}

export function buildValuationOutputState(assumptions?: SavedOutputContext, modelType = "fcff_dcf") {
  const output = assumptions?.outputs;
  const reasons: string[] = [];
  const currencyText = assumptions?.cash_flow_currency?.trim().toUpperCase();
  const currency = currencyText && /^[A-Z]{3}$/.test(currencyText) ? currencyText : null;
  const diagnosticWarnings = output ? diagnostics(output.warnings_json) : [];
  if (!output) reasons.push("No saved output. Save and calculate a valid assumption set.");
  if (assumptions?.is_stale) reasons.push("Saved assumptions are stale. Review the Assumption Ledger and rerun.");
  if (invalidDcfAssumptions(assumptions, modelType).length) reasons.push("Saved model inputs are missing or invalid. Correct them and rerun.");
  if (output && (!assumptions?.id || output.assumption_set_id !== assumptions.id)) reasons.push("Output does not match the saved assumption set.");
  if (output && !currency) reasons.push("Saved output currency is not configured. Review and save a currency; no currency is inferred.");
  const discountCurrency = assumptions?.discount_rate_currency?.trim().toUpperCase();
  if (discountCurrency && (!/^[A-Z]{3}$/.test(discountCurrency) || (currency !== discountCurrency && !assumptions?.currency_override_note?.trim()))) {
    reasons.push("Saved cash-flow and discount-rate currencies require review.");
  }
  if (diagnosticWarnings.some(w => w.severity === "critical" || w.severity === "blocking")) reasons.push("Critical, blocking, or unrecognized diagnostics require review and a new calculation.");
  const rawScore = output?.model_quality_score;
  return { output, currency, reasons, blocked: reasons.length > 0, diagnosticWarnings,
    score: finiteOutput(rawScore) && rawScore >= 0 && rawScore <= 100 ? rawScore : null,
    assumptionId: assumptions?.id, savedAt: assumptions?.updated_at, calculatedAt: output?.created_at,
  };
}

export type ValuationOutputState = ReturnType<typeof buildValuationOutputState>;

export function outputMoney(value: unknown, state: ValuationOutputState): string {
  if (!state.output) return "Not available";
  if (state.blocked) return "Not shown";
  if (!finiteOutput(value) || !state.currency) return "Not available";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: state.currency, maximumFractionDigits: 2 }).format(value);
}

export function outputGap(state: ValuationOutputState): string {
  if (!state.output) return "Not available";
  if (state.blocked) return "Not shown";
  const { current_market_price: price, intrinsic_value_per_share: estimate, upside_downside_pct: gap } = state.output;
  if (!finiteOutput(price) || price <= 0 || !finiteOutput(estimate) || !finiteOutput(gap) || !Number.isFinite(gap * 100)) return "Not available";
  return `${(gap * 100).toFixed(1)}%`;
}
