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
    <header className="page-header">
      <div className="page-header-copy">
        <p className="eyebrow">{eyebrow}</p>
        <div className="page-header-title-row">
          <h1>{title}</h1>
          {badge}
        </div>
      </div>
      {status ? <p className="page-header-status">{status}</p> : null}
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
