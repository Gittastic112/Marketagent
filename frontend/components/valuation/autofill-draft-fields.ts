import type { AssumptionProvenance, Company } from "@/lib/api";

export type FieldDefinition = {
  key: string;
  label: string;
  required?: boolean;
  formName?: string;
};

export const FIELD_GROUPS: Array<{ title: string; fields: FieldDefinition[]; }> = [
  {
    title: "Forecast Structure",
    fields: [
      { key: "projection_years_count", label: "Projection Years", formName: "projection_years" },
    ],
  },
  {
    title: "Operating Assumptions",
    fields: [
      { key: "starting_revenue", label: "Starting Revenue" },
      { key: "current_operating_margin", label: "Current Operating Margin" },
      { key: "target_operating_margin", label: "Target Operating Margin" },
      { key: "tax_rate", label: "Tax Rate" },
      { key: "sales_to_capital_ratio", label: "Sales to Capital Ratio" },
      { key: "starting_invested_capital", label: "Starting Invested Capital" },
    ],
  },
  {
    title: "Discount Rate and Terminal Value",
    fields: [
      { key: "risk_free_rate", label: "Risk-Free Rate" },
      { key: "equity_risk_premium", label: "Equity Risk Premium" },
      { key: "beta", label: "Beta" },
      { key: "cost_of_equity", label: "Cost of Equity" },
      { key: "pre_tax_cost_of_debt", label: "Pre-Tax Cost of Debt" },
      { key: "debt_to_capital", label: "Debt to Capital" },
      { key: "equity_to_capital", label: "Equity to Capital" },
      { key: "wacc_start", label: "Starting WACC" },
      { key: "wacc_terminal", label: "Terminal WACC" },
      { key: "terminal_growth_rate", label: "Terminal Growth Rate" },
      { key: "terminal_roic", label: "Terminal ROIC" },
    ],
  },
  {
    title: "Equity Bridge",
    fields: [
      { key: "cash", label: "Cash" },
      { key: "debt", label: "Debt" },
      { key: "cross_holdings", label: "Cross Holdings", required: false },
      { key: "operating_leases", label: "Operating Leases", required: false },
      { key: "minority_interests", label: "Minority Interests" },
      { key: "preferred_stock", label: "Preferred Stock" },
      { key: "employee_options_value", label: "Employee Options Value" },
      { key: "diluted_shares", label: "Diluted Shares" },
      { key: "basic_shares", label: "Basic Shares", required: false },
      { key: "current_market_price", label: "Comparison Price (optional)", required: false },
    ],
  },
  {
    title: "Equity Cash Flow and Payout Inputs",
    fields: [
      { key: "net_income", label: "Net Income", required: false },
      { key: "capex", label: "Capital Expenditure", required: false },
      { key: "depreciation", label: "Depreciation", required: false },
      { key: "change_in_nwc", label: "Change in Net Working Capital", required: false },
      { key: "new_debt_issued", label: "New Debt Issued", required: false },
      { key: "debt_repaid", label: "Debt Repaid", required: false },
      { key: "dividends", label: "Dividends", required: false },
      { key: "buybacks", label: "Buybacks", required: false },
      { key: "stock_issuances", label: "Stock Issuances", required: false },
    ],
  },
  {
    title: "Lifecycle and Special-Case Inputs",
    fields: [
      { key: "company_age", label: "Company Age", required: false },
      { key: "probability_of_failure", label: "Probability of Failure", required: false },
      { key: "distress_sale_proceeds", label: "Distress Sale Proceeds", required: false },
      { key: "book_value_of_equity", label: "Book Value of Equity", required: false },
      { key: "target_roe", label: "Target ROE", required: false },
    ],
  },
];

export const TEXT_FIELDS = [
  { key: "cash_flow_currency", label: "Cash-Flow Currency", required: true },
  { key: "discount_rate_currency", label: "Discount-Rate Currency", required: true },
  { key: "currency_override_note", label: "Currency Override Note", required: false },
  { key: "story_text", label: "Valuation Story", required: false },
  { key: "growth_story", label: "Growth Story", required: false },
  { key: "margin_story", label: "Margin Story", required: false },
  { key: "reinvestment_story", label: "Reinvestment Story", required: false },
  { key: "risk_story", label: "Risk Story", required: false },
];

export const RENDERED_FIELDS = new Set([
  "revenue_growth_years_json",
  ...TEXT_FIELDS.map((field) => field.key),
  ...FIELD_GROUPS.flatMap((group) => group.fields.map((field) => field.key)),
]);

export function provenanceEntry(
  value: AssumptionProvenance | string | undefined,
): AssumptionProvenance {
  return typeof value === "object" && value !== null ? value : {};
}

export function sourceBadgeClass(entry: AssumptionProvenance): string {
  if (entry.is_placeholder) return "badge badge-warn";
  if (entry.requires_review) return "badge badge-danger";
  return "badge badge-success";
}
