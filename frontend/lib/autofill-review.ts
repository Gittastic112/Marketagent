import type { AssumptionProvenance, AutofillSourceMetadata } from "./api";

const POSITIVE_FIELDS = new Set([
  "starting_revenue",
  "sales_to_capital_ratio",
  "starting_invested_capital",
  "diluted_shares",
  "current_market_price",
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
]);

export function reviewFieldValueIsValid(field: string, value: unknown): boolean {
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
