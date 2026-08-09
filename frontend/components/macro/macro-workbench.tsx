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

export function ClaimTypeBadges() {
  return (
    <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginBottom: "1rem" }}>
      {["Fact", "Calculation", "Source Summary", "User Assumption"].map((label) => (
        <span key={label} className="badge">
          {label}
        </span>
      ))}
    </div>
  );
}

export function MacroLimitationsNotice() {
  return (
    <div className="section-block" style={{ marginBottom: "1rem" }}>
      <strong>Required interpretation guardrails</strong>
      <ul style={{ marginBottom: 0 }}>
        <li>Coefficient signs are preserved from the source file.</li>
        <li>Macro scenarios do not mutate DCF assumptions automatically.</li>
        <li>Currency direction must be defined for currency shocks.</li>
        <li>Missing SIC coverage reduces confidence.</li>
      </ul>
    </div>
  );
}
