import type { BottomUpMacroSegment, TopDownMacroPeriod } from "./api/macro.ts";

export type MacroWorkbenchTab = "series" | "sector" | "scenario" | "top-down" | "bottom-up";

export const MACRO_WORKBENCH_TABS: Array<{ id: MacroWorkbenchTab; label: string }> = [
  { id: "series", label: "Series" },
  { id: "sector", label: "Sector Lookup" },
  { id: "scenario", label: "Scenario" },
  { id: "top-down", label: "Top-Down" },
  { id: "bottom-up", label: "Bottom-Up" },
];

export function normalizeMacroWorkbenchTab(value: string | string[] | undefined): MacroWorkbenchTab {
  const raw = Array.isArray(value) ? value[0] : value;
  const normalized = raw?.trim().toLowerCase();
  if (normalized && MACRO_WORKBENCH_TABS.some((tab) => tab.id === normalized)) {
    return normalized as MacroWorkbenchTab;
  }
  return "series";
}

export function macroNumber(value: string | undefined, label: string): number {
  const text = value?.trim() ?? "";
  if (!text || !/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$/i.test(text) || !Number.isFinite(Number(text))) {
    throw new Error("Enter a finite number for " + label + ". Use 0 only when zero is intended.");
  }
  return Number(text);
}

export function macroPeriodCount(value: string | undefined): number {
  if (!value) return 3;
  const count = Number(value);
  if (!Number.isInteger(count) || count < 3 || count > 24) throw new Error("Choose between 3 and 24 periods.");
  return count;
}

export function macroTopDownPeriods(values: Record<string, string>): TopDownMacroPeriod[] {
  return Array.from({length: macroPeriodCount(values.period_count)}, (_, offset) => {
    const index = offset + 1;
    const period = values["period_" + index]?.trim();
    if (!period) throw new Error("Enter the label for period " + index + ".");
    return {
      period_label: period,
      operating_income: macroNumber(values["operating_income_" + index], "period " + index + " operating income"),
      market_cap: macroNumber(values["market_cap_" + index], "period " + index + " market cap"),
      total_debt: macroNumber(values["total_debt_" + index], "period " + index + " debt"),
      change_in_long_term_bond_rate: macroNumber(values["rate_change_" + index], "period " + index + " rate change"),
      gdp_growth: macroNumber(values["gdp_growth_" + index], "period " + index + " GDP growth"),
      inflation_change: macroNumber(values["inflation_change_" + index], "period " + index + " inflation change"),
      currency_change: macroNumber(values["currency_change_" + index], "period " + index + " currency change"),
    };
  });
}

export function macroBottomUpSegments(values: Record<string, string>): BottomUpMacroSegment[] {
  const segments: BottomUpMacroSegment[] = [];
  for (const index of [1, 2, 3]) {
    const name = values["segment_" + index + "_name"]?.trim() ?? "";
    const sic = values["segment_" + index + "_sic"]?.trim() ?? "";
    const value = values["segment_" + index + "_value"]?.trim() ?? "";
    if (!name && !sic && !value) continue;
    if (!name || !sic) throw new Error("Complete the name, SIC and value for segment " + index + ".");
    const amount = macroNumber(value, "segment " + index + " value");
    if (amount < 0) throw new Error("Segment values cannot be negative.");
    segments.push({segment_name: name, sic_code: sic, segment_value: amount});
  }
  if (!segments.length) throw new Error("Enter at least one complete segment.");
  return segments;
}
