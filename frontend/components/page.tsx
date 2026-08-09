import type { ReactNode } from "react";

export function PageHeader({
  eyebrow,
  title,
  status,
  badge
}: {
  eyebrow: string;
  title: string;
  status?: string;
  badge?: ReactNode;
}) {
  return (
    <header className="page-header" style={{ display: "flex", flexDirection: "column", gap: "0.25rem", marginBottom: "2rem" }}>
      <p className="eyebrow" style={{ margin: 0, fontSize: "0.85rem", fontWeight: 600, color: "var(--accent)", textTransform: "uppercase", letterSpacing: "0.05em" }}>{eyebrow}</p>
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
        <h1 style={{ margin: 0, fontSize: "2.25rem", fontWeight: 700, letterSpacing: 0 }}>{title}</h1>
        {badge}
        {status ? <span style={{ fontSize: "0.95rem", color: "var(--muted)", fontWeight: 500, alignSelf: "flex-end", paddingBottom: "0.3rem" }}>• {status}</span> : null}
      </div>
    </header>
  );
}

export function Panel({
  title,
  children,
  className,
}: {
  title: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={["panel", className].filter(Boolean).join(" ")}>
      <div className="panel-header">
        <h2>{title}</h2>
      </div>
      <div className="panel-content">
        {children}
      </div>
    </section>
  );
}

export {
  EmptyState,
  ErrorState,
  LoadingState,
  MockDataBadge,
  MockDataState,
  StaleDataBanner,
  PartialDataNotice,
  NotConfiguredState,
  DataFreshnessIndicator,
  UnsupportedState,
  ManualDataBadge,
  PrototypeBadge,
  SourceBadge,
  ConfidenceIndicator,
  ReviewStateBadge
} from "./ui/data-states";
