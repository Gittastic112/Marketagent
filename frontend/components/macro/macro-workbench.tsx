import Link from "next/link";

import { MACRO_WORKBENCH_TABS, type MacroWorkbenchTab } from "@/lib/macro-workbench";

export function MacroWorkbenchTabs({ activeTab }: { activeTab: MacroWorkbenchTab }) {
  return (
    <div style={{ display: "flex", gap: "0.5rem", borderBottom: "1px solid var(--line)", marginBottom: "1.5rem", flexWrap: "wrap" }}>
      {MACRO_WORKBENCH_TABS.map((tab) => (
        <Link
          key={tab.id}
          href={`/macro?tab=${tab.id}`}
          className={activeTab === tab.id ? "btn btn-primary" : "secondary-button"}
          style={{ padding: "0.45rem 0.85rem", fontSize: "0.875rem", marginBottom: "-1px" }}
        >
          {tab.label}
        </Link>
      ))}
    </div>
  );
}

export function ClaimTypeBadges({activeTab}: {activeTab: MacroWorkbenchTab}) {
  const labels = activeTab === "top-down" ? ["User Assumption", "Calculation"]
    : activeTab === "sector" || activeTab === "series" ? ["Source Summary"]
    : ["Source Summary", "User Assumption", "Calculation"];
  return (
    <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginBottom: "1rem" }}>
      {labels.map((label) => (
        <span key={label} className="badge">
          {label}
        </span>
      ))}
    </div>
  );
}

export function MacroLimitationsNotice() {
  return (
    <details className="section-block" style={{ marginBottom: "1rem" }}>
      <summary>How to interpret macro results</summary>
      <ul style={{ marginBottom: 0 }}>
        <li>Coefficient signs are preserved from the source file.</li>
        <li>These scenarios leave your saved valuation assumptions unchanged.</li>
        <li>Currency direction must be defined for currency shocks.</li>
        <li>Missing coefficients withhold full-company estimates; covered contributions stay visible.</li>
      </ul>
    </details>
  );
}
