import type { CurrencyConsistencyCheck } from "@/lib/valuation-context";

export function CurrencyConsistencyWarning({ check }: { check: CurrencyConsistencyCheck | null }) {
  if (!check || check.severity === "ok") return null;

  const isBlocking = check.severity === "blocking";
  const bgColor = isBlocking ? "rgba(220,38,38,0.1)" : "rgba(245,158,11,0.1)";
  const borderColor = isBlocking ? "var(--danger)" : "var(--warning)";

  return (
    <div style={{ padding: "1rem", background: bgColor, borderLeft: `4px solid ${borderColor}`, borderRadius: "0 4px 4px 0", marginBottom: "1.5rem" }}>
      <strong style={{ display: "block", marginBottom: "0.25rem", color: isBlocking ? "var(--danger)" : "var(--warning)" }}>
        {isBlocking ? "Blocking Issue" : "Warning"}
      </strong>
      <div style={{ fontSize: "0.9rem", color: "var(--text)" }}>{check.message}</div>
    </div>
  );
}
