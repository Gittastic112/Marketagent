export type WorkspaceTheme = "light" | "dark";
export const WORKSPACE_THEME_KEY = "marketagent:theme";

export function workspaceTheme(value: string | null): WorkspaceTheme {
  return value === "dark" ? "dark" : "light";
}

/** Only route families are shown; private IDs and query strings never enter the breadcrumb. */
export function workspaceLocation(pathname: string): string {
  const path = pathname.split(/[?#]/, 1)[0];
  const company = path.match(/^\/companies\/[^/]+(?:\/([^/]+))?/);
  if (company) {
    const sections: Record<string, string> = {
      valuation: "Company valuation", fundamentals: "Company financials", thesis: "Investment thesis",
      decisions: "Decision journal", filings: "Company filings", evidence: "Company evidence", setup: "Company setup",
    };
    return sections[company[1]] || "Company overview";
  }
  const routes: [string, string][] = [
    ["/research/sessions", "Research sessions"], ["/research-lab", "Research Lab"], ["/portfolio/regime", "Market regime"],
    ["/valuation/quick", "Quick valuation"], ["/intelligence/review", "Contradiction review"],
    ["/admin/damodaran", "Benchmark data"], ["/daily-brief", "Daily brief"],
    ["/data-health", "Data health"], ["/thesis-notes", "Research notes"],
    ["/companies", "Companies"], ["/portfolio", "Portfolio"], ["/valuation", "Valuations"],
    ["/research", "Research library"], ["/documents", "Source documents"], ["/events", "Events"],
    ["/narratives", "Narratives"], ["/alerts", "Alerts"], ["/settings", "Settings"],
    ["/search", "Search evidence"], ["/sources", "Sources"], ["/data", "Source activity"],
    ["/macro", "Macro"], ["/evaluations", "Extraction evaluations"], ["/advanced", "Advanced tools"],
  ];
  return routes.find(([route]) => path === route || path.startsWith(`${route}/`))?.[1]
    ?? (path === "/" ? "Today" : "Research workspace");
}

export function isWorkspaceSearchShortcut(event: { key: string; metaKey: boolean; ctrlKey: boolean; altKey: boolean; shiftKey: boolean; defaultPrevented: boolean }, editing: boolean): boolean {
  return !editing && !event.defaultPrevented && !event.altKey && !event.shiftKey
    && (event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k";
}
