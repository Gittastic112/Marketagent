import type { ReactNode } from "react";

export function PageHeader({
  eyebrow,
  title,
  status,
  badge,
  description,
  actions,
}: {
  eyebrow: string;
  title: string;
  status?: string;
  badge?: ReactNode;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <header className="page-header">
      <div className="page-header-copy">
        <p className="eyebrow">{eyebrow}</p>
        <div className="page-header-title-row">
          <h1>{title}</h1>
          {badge}
        </div>
        {description && <p className="page-description">{description}</p>}
      </div>
      <div className="page-header-actions">
        {status ? <p className="page-header-status">{status}</p> : null}
        {actions}
      </div>
    </header>
  );
}

export function Panel({
  title,
  children,
  className,
  actions,
  collapsible = false,
}: {
  title: ReactNode;
  children: ReactNode;
  className?: string;
  actions?: ReactNode;
  collapsible?: boolean;
}) {
  if (collapsible) return <details className={["panel", "panel-disclosure", className].filter(Boolean).join(" ")}>
    <summary className="panel-header"><h2>{title}</h2>{actions}</summary>
    <div className="panel-content">{children}</div>
  </details>;
  return (
    <section className={["panel", className].filter(Boolean).join(" ")}>
      <div className="panel-header">
        <h2>{title}</h2>
        {actions}
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
  UnavailableDataNotice,
  DataStateNotices,
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
