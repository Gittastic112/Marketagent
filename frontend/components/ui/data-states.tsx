import type { ReactNode } from "react";
import type { ApiMeta, ApiErrorDetail } from "@/lib/api";
import { buildDataStateBadges, summarizeApiMetas, type DataStateTone } from "@/lib/data-state-meta";

export function LoadingState({ message = "Loading..." }: { message?: string }) {
  return (
    <div role="status" aria-live="polite" style={{ padding: "2rem", textAlign: "center", color: "var(--text-secondary)", fontSize: "0.9rem" }}>
      <div className="spinner" style={{ marginBottom: "1rem" }}></div>
      {message}
    </div>
  );
}

export function ErrorState({ message, errors }: { message?: string; errors?: ApiErrorDetail[] }) {
  if (errors && errors.length > 0 && (errors[0].code === "AUTH_NOT_CONFIGURED" || errors[0].code === "NOT_CONFIGURED")) {
    return <NotConfiguredState title="Service Not Configured" description={errors[0].message} />;
  }

  return (
    <div role="alert" style={{ padding: "1.5rem", border: "1px solid var(--error-color, #ef4444)", borderRadius: "8px", backgroundColor: "rgba(239, 68, 68, 0.05)", margin: "1rem 0" }}>
      <h3 style={{ color: "var(--error-color, #ef4444)", fontSize: "1rem", margin: "0 0 0.5rem 0" }}>
        {message || "Could not load data"}
      </h3>
      {errors && errors.length > 0 && (
        <ul style={{ margin: 0, paddingLeft: "1.5rem", color: "var(--text-secondary)", fontSize: "0.85rem" }}>
          {errors.map((err, i) => (
            <li key={i} style={{ marginBottom: "0.25rem" }}>
              <strong>{err.code}</strong>: {err.message}
              {err.field && <span> (Field: <code>{err.field}</code>)</span>}
              {err.target && <span> [Target: {err.target}]</span>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function EmptyState({ label }: { label: string }) {
  return <div className="empty">{label}</div>;
}

export function StaleDataBanner({ message, lastUpdated }: { message?: string; lastUpdated?: string }) {
  return (
    <div style={{
      padding: "10px 14px",
      borderRadius: "6px",
      background: "rgba(249, 115, 22, 0.1)",
      border: "1px solid rgba(249, 115, 22, 0.2)",
      color: "var(--text-secondary)",
      fontSize: "0.85rem",
      display: "flex",
      alignItems: "center",
      gap: "10px",
      marginBottom: "1rem"
    }}>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="rgb(249, 115, 22)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <polyline points="12 6 12 12 16 14"></polyline>
      </svg>
      <div>
        <span style={{ color: "var(--warning-text)", fontWeight: 500 }}>Older source data</span>
        {` - ${message || "Stored source data is older than its freshness threshold. Refresh or re-run the owning source."}`}
        {lastUpdated ? ` (Last updated: ${new Date(lastUpdated).toLocaleString()})` : ""}
      </div>
    </div>
  );
}

export function UnavailableDataNotice({ message }: { message?: string }) {
  return (
    <div style={{
      padding: "10px 14px",
      borderRadius: "6px",
      background: "rgba(239, 68, 68, 0.06)",
      border: "1px solid rgba(239, 68, 68, 0.24)",
      color: "var(--text-secondary)",
      fontSize: "0.85rem",
      display: "flex",
      alignItems: "center",
      gap: "10px",
      marginBottom: "1rem"
    }} role="status">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--error-color, #ef4444)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="8" x2="12" y2="12"></line>
        <line x1="12" y1="16" x2="12.01" y2="16"></line>
      </svg>
      <span>
        <strong style={{ color: "var(--error-color, #ef4444)" }}>Data unavailable: </strong>
        {message || "The request failed. No cached replacement is being shown."}
      </span>
    </div>
  );
}

export function MockDataBadge() {
  return (
    <span style={{ fontSize: "var(--font-size-xs)", padding: "0.1rem 0.4rem", backgroundColor: "var(--surface-muted)", border: "1px dashed var(--border-color)", borderRadius: "4px", color: "var(--text)", textTransform: "uppercase", letterSpacing: "0.04em", verticalAlign: "middle" }}>
      Mock Data
    </span>
  );
}

export function MockDataState({ message }: { message: string }) {
  return (
    <div style={{
      padding: "12px 16px",
      borderRadius: "8px",
      background: "rgba(234, 179, 8, 0.1)",
      border: "1px dashed rgba(234, 179, 8, 0.4)",
      color: "var(--text-secondary)",
      fontSize: "0.9rem",
      display: "flex",
      alignItems: "center",
      gap: "10px",
      marginBottom: "2rem"
    }}>
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgb(234, 179, 8)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="8" x2="12" y2="12"></line>
        <line x1="12" y1="16" x2="12.01" y2="16"></line>
      </svg>
      <div>
        <strong style={{ color: "var(--warning-text)", display: "block", marginBottom: "2px" }}>Mock Data</strong>
        {message}
      </div>
    </div>
  );
}

export function ManualDataState({ message }: { message: string }) {
  return (
    <div style={{
      padding: "12px 16px",
      borderRadius: "8px",
      background: "rgba(59, 130, 246, 0.1)",
      border: "1px dashed rgba(59, 130, 246, 0.4)",
      color: "var(--text-secondary)",
      fontSize: "0.9rem",
      display: "flex",
      alignItems: "center",
      gap: "10px",
      marginBottom: "2rem"
    }}>
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgb(59, 130, 246)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 20h9"></path>
        <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
      </svg>
      <div>
        <strong style={{ color: "var(--color-info)", display: "block", marginBottom: "2px" }}>Manual Data</strong>
        {message}
      </div>
    </div>
  );
}

export function NotConfiguredState({ sourceName, title, description, actionText, onAction, message }: { sourceName?: string, title?: string, description?: string, actionText?: string, onAction?: () => void, message?: string }) {
  return (
    <div style={{
      padding: "2rem",
      borderRadius: "8px",
      background: "var(--surface)",
      border: "1px dashed var(--border)",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      textAlign: "center",
      gap: "12px",
      color: "var(--text-secondary)",
      margin: "1rem 0"
    }}>
      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--muted)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="3"></circle>
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
      </svg>
      <div>
        <h3 style={{ margin: "0 0 4px 0", color: "var(--text-primary)", fontSize: "1.1rem" }}>{title || `${sourceName} Not Configured`}</h3>
        <p style={{ margin: 0, fontSize: "0.9rem" }}>{description || message || `Please configure the API keys or settings for ${sourceName} to enable this feature.`}</p>
      </div>
      {actionText && (
        <button
          onClick={onAction}
          style={{
            marginTop: "8px",
            padding: "8px 16px",
            background: "var(--text-primary)",
            color: "var(--bg)",
            border: "none",
            borderRadius: "6px",
            fontSize: "0.85rem",
            fontWeight: 500,
            cursor: "pointer",
            transition: "opacity 0.2s"
          }}
          onMouseOver={(e) => e.currentTarget.style.opacity = "0.9"}
          onMouseOut={(e) => e.currentTarget.style.opacity = "1"}
        >
          {actionText}
        </button>
      )}
    </div>
  );
}

export function PartialDataNotice({ message, title = "Data coverage" }: { message: string; title?: string }) {
  return (
    <div style={{
      padding: "10px 14px",
      borderRadius: "6px",
      background: "rgba(59, 130, 246, 0.1)",
      border: "1px solid rgba(59, 130, 246, 0.2)",
      color: "var(--text-secondary)",
      fontSize: "0.85rem",
      display: "flex",
      alignItems: "center",
      gap: "10px",
      marginBottom: "1rem"
    }}>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="rgb(59, 130, 246)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 12A10 10 0 1 1 12 2v0"></path>
      </svg>
      <span>
        <strong style={{ color: "var(--color-info)" }}>{title}: </strong>
        {message}
      </span>
    </div>
  );
}

export function DataStateNotices({
  metas,
  staleMessage,
  partialMessage,
  unavailableMessage,
  mockMessage,
  manualMessage
}: {
  metas: Array<ApiMeta | null | undefined>;
  staleMessage?: string;
  partialMessage?: string;
  unavailableMessage?: string;
  mockMessage?: string;
  manualMessage?: string;
}) {
  const dataState = summarizeApiMetas(metas);
  const unavailableText = unavailableMessage || (dataState.allUnavailable
    ? "Data could not be loaded. Try again from the affected section."
    : "Some sections could not load. The other sections remain available.");
  const freshnessText = (dataState.allStale ? staleMessage : partialMessage)
    || "Check the source date before using these figures. Refresh the relevant source when needed.";
  const displayedMessages = [
    ...(dataState.someUnavailable ? [unavailableText] : []),
    ...(dataState.someStale ? [freshnessText] : []),
    ...(dataState.hasMock && mockMessage ? [mockMessage] : []),
    ...(dataState.hasManual && !dataState.hasMock && manualMessage ? [manualMessage] : []),
  ].map(message => message.trim());
  const warnings = dataState.warnings.filter(warning => !displayedMessages.includes(warning));

  return (
    <>
      {dataState.allUnavailable && <UnavailableDataNotice message={unavailableText} />}
      {!dataState.allUnavailable && dataState.someUnavailable && (
        <PartialDataNotice title="Some sections could not load" message={unavailableText} />
      )}
      {dataState.someStale && <StaleDataBanner message={freshnessText} />}
      {dataState.hasMock && (
        <MockDataState message={mockMessage || "One or more panels are using mock data. Treat affected values as placeholders."} />
      )}
      {dataState.hasManual && !dataState.hasMock && (
        <ManualDataState message={manualMessage || "One or more panels are using manual overrides. Treat affected values as user-specified."} />
      )}
      {warnings.length > 0 && (
        <div style={{
          padding: "10px 14px",
          borderRadius: "6px",
          background: "var(--surface)",
          border: "1px solid var(--border)",
          color: "var(--text-secondary)",
          fontSize: "0.85rem",
          display: "flex",
          flexDirection: "column",
          gap: "4px",
          marginBottom: "1rem"
        }}>
          <strong>Data notes</strong>
          <p style={{ margin: 0 }}>{warnings[0]}</p>
          {warnings.length > 1 && <details>
            <summary>Show {warnings.length - 1} more data note{warnings.length === 2 ? "" : "s"}</summary>
            <ul style={{ margin: "0.5rem 0 0", paddingLeft: "1.5rem" }}>
              {warnings.slice(1).map(warning => <li key={warning}>{warning}</li>)}
            </ul>
          </details>}
        </div>
      )}
    </>
  );
}

function badgeColor(tone: DataStateTone) {
  if (tone === "success") {
    return "var(--success-color, #4CAF50)";
  }
  if (tone === "warning") {
    return "var(--warning-text)";
  }
  if (tone === "danger") {
    return "var(--error-color, #ef4444)";
  }
  return "var(--text-muted)";
}

export function DataFreshnessIndicator({ meta, lastUpdated, source }: { meta?: ApiMeta, lastUpdated?: string, source?: string }) {
  if (meta) {
    const badges = buildDataStateBadges(meta);

    return (
      <div style={{ fontSize: "var(--font-size-xs)", color: "var(--text-secondary)", display: "flex", alignItems: "center", gap: "0.5rem" }}>
        {badges.map((badge) => {
          if (badge.label === "Mock Data") {
            return <MockDataBadge key={badge.label} />;
          }
          if (badge.label === "Manual Data") {
            return <ManualDataBadge key={badge.label} />;
          }
          return <span key={badge.label} style={{ color: badgeColor(badge.tone) }}>{badge.label}</span>;
        })}
      </div>
    );
  }

  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      gap: "6px",
      fontSize: "var(--font-size-xs)",
      color: "var(--muted)",
      marginTop: "8px"
    }}>
      <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: "rgb(34, 197, 94)" }}></div>
      <span>Updated {lastUpdated}</span>
      {source && <span>• Source: {source}</span>}
    </div>
  );
}

export function UnsupportedState({ message = "This feature is currently unsupported in this context." }: { message?: string }) {
  return (
    <div style={{
      padding: "16px",
      borderRadius: "8px",
      background: "var(--surface)",
      border: "1px dashed var(--border)",
      color: "var(--text-secondary)",
      fontSize: "0.9rem",
      textAlign: "center",
      margin: "1rem 0"
    }}>
      <p style={{ margin: 0 }}>{message}</p>
    </div>
  );
}

export function ManualDataBadge() {
  return (
    <span style={{ fontSize: "var(--font-size-xs)", padding: "0.1rem 0.4rem", backgroundColor: "rgba(59, 130, 246, 0.1)", border: "1px solid rgba(59, 130, 246, 0.3)", borderRadius: "4px", color: "#1d4ed8", textTransform: "uppercase", letterSpacing: "0.04em", verticalAlign: "middle" }}>
      Manual Data
    </span>
  );
}

export function PrototypeBadge() {
  return (
    <span style={{ fontSize: "var(--font-size-xs)", padding: "0.1rem 0.4rem", backgroundColor: "rgba(168, 85, 247, 0.1)", border: "1px solid rgba(168, 85, 247, 0.3)", borderRadius: "4px", color: "#6b21a8", textTransform: "uppercase", letterSpacing: "0.04em", verticalAlign: "middle" }}>
      Prototype
    </span>
  );
}

export function SourceBadge({ source }: { source: string }) {
  return (
    <span style={{ fontSize: "var(--font-size-xs)", padding: "0.1rem 0.4rem", backgroundColor: "var(--surface)", border: "1px solid var(--border)", borderRadius: "4px", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.04em", verticalAlign: "middle" }}>
      {source}
    </span>
  );
}

export function ConfidenceIndicator({ level }: { level: "high" | "medium" | "low" | "none" }) {
  const colors = {
    high: "rgb(34, 197, 94)",
    medium: "rgb(234, 179, 8)",
    low: "rgb(249, 115, 22)",
    none: "var(--muted)"
  };

  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: "4px", fontSize: "var(--font-size-xs)", color: "var(--text-secondary)", verticalAlign: "middle" }}>
      <div style={{ width: "6px", height: "6px", borderRadius: "50%", background: colors[level] || colors.none }}></div>
      <span style={{ textTransform: "capitalize" }}>{level} Confidence</span>
    </span>
  );
}

export function ReviewStateBadge({ state }: { state: "reviewed" | "unreviewed" | "needs_review" }) {
  const styles = {
    reviewed: { color: "#166534", bg: "rgba(34, 197, 94, 0.1)", border: "rgba(34, 197, 94, 0.3)" },
    unreviewed: { color: "var(--text-secondary)", bg: "var(--surface)", border: "var(--border)" },
    needs_review: { color: "#854d0e", bg: "rgba(234, 179, 8, 0.1)", border: "rgba(234, 179, 8, 0.3)" }
  };

  const current = styles[state] || styles.unreviewed;
  const label = state.replace("_", " ");

  return (
    <span style={{ fontSize: "var(--font-size-xs)", padding: "0.1rem 0.4rem", backgroundColor: current.bg, border: `1px solid ${current.border}`, borderRadius: "4px", color: current.color, textTransform: "capitalize", verticalAlign: "middle" }}>
      {label}
    </span>
  );
}
