import type { DcfProjectionYear } from "./api/valuation.ts";

type Column = { key: keyof DcfProjectionYear; label: string; percent?: boolean };

export function projectionColumns(modelType: string): Column[] {
  if (modelType === "financial_services") return [
    { key: "invested_capital", label: "Opening book equity" },
    { key: "revenue_growth", label: "Book equity growth", percent: true },
    { key: "nopat", label: "Net income" },
    { key: "roic", label: "ROE", percent: true },
    { key: "wacc", label: "Cost of equity", percent: true },
    { key: "fcff", label: "Excess return" },
    { key: "pv_fcff", label: "PV of excess return" },
  ];
  return [
    { key: "revenue", label: "Revenue" },
    { key: "revenue_growth", label: "Growth", percent: true },
    { key: "ebit_margin", label: "EBIT margin", percent: true },
    { key: "nopat", label: "NOPAT" },
    { key: "reinvestment", label: "Reinvestment" },
    { key: "fcff", label: "FCFF" },
    { key: "roic", label: "ROIC", percent: true },
    { key: "wacc", label: "WACC", percent: true },
    { key: "pv_fcff", label: "PV of FCFF" },
  ];
}

export function projectionDescription(modelType: string): string {
  const timing = "Projection years are relative periods, not calendar dates. A reviewed fiscal-year anchor has not been established.";
  if (modelType === "financial_services") return `${timing} Simplified constant book-equity growth and linear ROE fade, not a regulatory-capital or payout forecast.`;
  if (modelType === "distressed") return `${timing} These operating projections are conditional on survival, not a decomposition of the final probability-weighted equity value.`;
  return `${timing} Calculations use saved User Assumptions, not verified future results.`;
}
