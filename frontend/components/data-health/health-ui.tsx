type HealthMetricTone = "neutral" | "success" | "warning" | "danger" | "muted";

export function formatDate(iso: string) {
  return new Date(iso).toLocaleString(undefined, { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

export function statusBadge(status: string) {
  const colors: Record<string, string> = {
    success: "var(--success)",
    completed: "var(--success)",
    working: "var(--success)",
    configured: "var(--accent)",
    failed: "var(--error)",
    error: "var(--error)",
    failing: "var(--error)",
    running: "var(--warning)",
    missing_key: "var(--warning)",
    not_configured: "var(--warning)",
    not_available: "var(--text-secondary)",
    manual_only: "var(--text-secondary)",
    unsupported_market: "var(--text-secondary)",
    unknown: "var(--text-secondary)",
    pending: "var(--text-secondary)",
    healthy: "var(--success)",
    passed: "var(--success)",
    partial: "var(--warning)",
    supported: "var(--success)",
    unsupported: "var(--error)",
    ingested: "var(--success)",
    metadata_only: "var(--warning)",
    not_ingested: "var(--text-secondary)",
    source_missing: "var(--error)",
    current: "var(--success)",
    stale: "var(--warning)",
    historical: "var(--text-secondary)",
    user_assumed_recent: "var(--accent)",
    complete: "var(--success)",
    missing: "var(--warning)",
    hash_mismatch: "var(--error)",
    blocked: "var(--error)",
    issues_found: "var(--error)",
    eligible: "var(--warning)",
    applied: "var(--success)",
    ambiguous_match: "var(--warning)",
    mock: "var(--warning)",
    prototype: "var(--accent)",
  };
  const normalized = status.toLowerCase();
  const color = colors[normalized] ?? colors[normalized.split(" ").at(-1) ?? ""] ?? "var(--text-secondary)";
  return (
    <span className="badge" style={{ backgroundColor: "var(--surface-muted)", color, border: `1px solid ${color}` }}>
      {status}
    </span>
  );
}

export function HealthMetric({
  label,
  value,
  detail,
  tone = "neutral",
  compact = false,
}: {
  label: string;
  value: string | number;
  detail?: string;
  tone?: HealthMetricTone;
  compact?: boolean;
}) {
  return (
    <article className={`health-metric-card${compact ? " health-metric-card-compact" : ""}`} data-tone={tone}>
      <span className="health-metric-label">{label}</span>
      <strong className="health-metric-value">{value}</strong>
      {detail ? <span className="health-metric-detail">{detail}</span> : null}
    </article>
  );
}
