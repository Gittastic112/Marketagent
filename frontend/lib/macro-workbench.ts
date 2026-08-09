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
