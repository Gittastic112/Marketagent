import type { AssumptionProvenance, AutofillSourceMetadata } from "./api";

const POSITIVE_FIELDS = new Set([
  "starting_revenue",
  "sales_to_capital_ratio",
  "starting_invested_capital",
  "diluted_shares",
  "cost_of_equity",
  "wacc_start",
  "wacc_terminal",
  "book_value_of_equity",
  "current_market_price",
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
  "probability_of_failure",
]);
const MARGIN_FIELDS = new Set(["current_operating_margin", "target_operating_margin", "target_roe"]);

export function reviewFieldValueIsValid(field: string, value: unknown): boolean {
  if (field === "current_market_price" && value === null) return true;
  if (field === "current_market_price" && typeof value !== "number" && typeof value !== "string") return false;
  if (value == null || typeof value === "boolean" || (typeof value === "string" && !value.trim())) {
    return false;
  }
  if (field === "cash_flow_currency" || field === "discount_rate_currency") {
    return typeof value === "string" && /^[A-Za-z]{3}$/.test(value.trim());
  }
  if (Array.isArray(value)) {
    return value.length > 0 && value.every((item) => typeof item === "number" && Number.isFinite(item));
  }
  if (value && typeof value === "object") {
    const entries = Object.values(value);
    return entries.length > 0 && entries.every((item) => typeof item === "number" && Number.isFinite(item));
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
  if (field === "projection_years_count") return Number.isInteger(numberValue) && numberValue >= 1 && numberValue <= 30;
  if (POSITIVE_FIELDS.has(field)) return numberValue > 0;
  if (NONNEGATIVE_FIELDS.has(field)) return numberValue >= 0;
  return true;
}

export function reviewFieldsForModel(metadata: AutofillSourceMetadata, modelType = "fcff_dcf"): string[] {
  return modelType === "fcff_dcf" ? metadata.review_fields : metadata.review_fields_by_model?.[modelType] ?? metadata.review_fields;
}

export function unresolvedReviewFields(
  sourceMetadata: AutofillSourceMetadata,
  reviewedFields: ReadonlySet<string>,
  values: Record<string, unknown>,
  modelType = "fcff_dcf",
): string[] {
  return reviewFieldsForModel(sourceMetadata, modelType).filter(
    (field) => !reviewedFields.has(field) || !reviewFieldValueIsValid(field, values[field]),
  );
}

export function provenanceLabel(entry: AssumptionProvenance | string | undefined): string {
  if (!entry) return "Unknown source";
  if (typeof entry === "string") return entry;
  return entry.label || entry.source_type || "Unknown source";
}
