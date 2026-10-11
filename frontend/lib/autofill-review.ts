import type { AssumptionProvenance, AutofillSourceMetadata } from "./api";

const POSITIVE_FIELDS = new Set([
  "starting_revenue",
  "sales_to_capital_ratio",
  "starting_invested_capital",
  "diluted_shares",
  "cost_of_equity",
  "wacc_start",
  "wacc_terminal",
]);
const NONNEGATIVE_FIELDS = new Set([
  "cash",
  "debt",
  "minority_interests",
  "preferred_stock",
  "employee_options_value",
  "cross_holdings",
  "operating_leases",
  "basic_shares",
  "distress_sale_proceeds",
]);
const UNIT_INTERVAL_FIELDS = new Set([
  "tax_rate",
  "risk_free_rate",
  "equity_risk_premium",
  "cost_of_equity",
  "pre_tax_cost_of_debt",
  "debt_to_capital",
  "equity_to_capital",
  "wacc_start",
  "wacc_terminal",
  "terminal_roic",
]);
const MARGIN_FIELDS = new Set(["current_operating_margin", "target_operating_margin"]);

export function reviewFieldValueIsValid(field: string, value: unknown): boolean {
  if (field === "cash_flow_currency" || field === "discount_rate_currency") {
    return typeof value === "string" && /^[A-Za-z]{3}$/.test(value.trim());
  }
  if (Array.isArray(value)) {
    return value.length > 0 && value.every((item) => typeof item === "number" && Number.isFinite(item));
  }
  if (value && typeof value === "object") {
    return Object.keys(value).length > 0;
  }

  const numberValue = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(numberValue)) {
    return false;
  }
  if (UNIT_INTERVAL_FIELDS.has(field)) {
    return (POSITIVE_FIELDS.has(field) ? numberValue > 0 : numberValue >= 0) && numberValue <= 1;
  }
  if (MARGIN_FIELDS.has(field)) return numberValue >= -1 && numberValue <= 1;
  if (field === "terminal_growth_rate") return numberValue >= -0.2 && numberValue <= 0.2;
  if (field === "beta") return numberValue >= 0 && numberValue <= 5;
  if (POSITIVE_FIELDS.has(field)) return numberValue > 0;
  if (NONNEGATIVE_FIELDS.has(field)) return numberValue >= 0;
  return true;
}

export function unresolvedReviewFields(
  sourceMetadata: AutofillSourceMetadata,
  reviewedFields: ReadonlySet<string>,
  values: Record<string, unknown>,
): string[] {
  return sourceMetadata.review_fields.filter(
    (field) => !reviewedFields.has(field) || !reviewFieldValueIsValid(field, values[field]),
  );
}

export function provenanceLabel(entry: AssumptionProvenance | string | undefined): string {
  if (!entry) return "Unknown source";
  if (typeof entry === "string") return entry;
  return entry.label || entry.source_type || "Unknown source";
}
