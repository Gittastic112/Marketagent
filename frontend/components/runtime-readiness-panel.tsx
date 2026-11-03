import type { ApiErrorDetail, RuntimeReadiness } from "@/lib/api";


function readinessTone(status: string) {
  return status === "ready" ? "success" : "danger";
}


export function RuntimeReadinessPanel({
  readiness,
  errors,
}: {
  readiness: RuntimeReadiness | null;
  errors: ApiErrorDetail[];
}) {
  const recoverySteps = readiness?.recovery_steps.length
    ? readiness.recovery_steps
    : readiness?.status === "ready"
      ? []
      : [
          "docker compose up --build -d",
          "docker compose exec backend alembic upgrade head",
        ];

  return (
    <section className="health-summary-section" aria-labelledby="runtime-readiness-title">
      <div className="health-section-heading">
        <div>
          <h2 id="runtime-readiness-title">Runtime readiness</h2>
          <p>Liveness only proves that a process exists. Readiness also verifies the database and required schema.</p>
        </div>
        <span className={`badge badge-${readiness?.status === "ready" ? "success" : "danger"}`}>
          {readiness?.status || "unavailable"}
        </span>
      </div>
      <div className="health-metric-grid runtime-readiness-grid">
        <article className="health-metric-card health-metric-card-compact" data-tone={readinessTone(readiness?.database_status || "unavailable")}>
          <span className="health-metric-label">Database</span>
          <strong className="health-metric-value">{readiness?.database_status || "Unavailable"}</strong>
        </article>
        <article className="health-metric-card health-metric-card-compact" data-tone={readinessTone(readiness?.schema_status || "unknown")}>
          <span className="health-metric-label">Schema</span>
          <strong className="health-metric-value">{readiness?.schema_status || "Unknown"}</strong>
        </article>
        <article className="health-metric-card health-metric-card-compact" data-tone={readiness?.current_migration_heads.includes(readiness.expected_migration_head) ? "success" : "danger"}>
          <span className="health-metric-label">Current migration</span>
          <strong className="health-metric-value runtime-migration-value">
            {readiness?.current_migration_heads.join(", ") || "Unavailable"}
          </strong>
        </article>
        <article className="health-metric-card health-metric-card-compact" data-tone="neutral">
          <span className="health-metric-label">Expected migration</span>
          <strong className="health-metric-value runtime-migration-value">
            {readiness?.expected_migration_head || "Unknown"}
          </strong>
        </article>
      </div>

      {(readiness?.missing_tables.length || readiness?.missing_columns.length || readiness?.missing_constraints.length) ? (
        <div className="runtime-readiness-blockers">
          <strong>Schema blockers</strong>
          <ul className="compact-list">
            {readiness.missing_tables.map((table) => <li key={`table-${table}`}>Missing table: {table}</li>)}
            {readiness.missing_columns.map((column) => <li key={`column-${column}`}>Missing column: {column}</li>)}
            {readiness.missing_constraints.map((constraint) => <li key={`constraint-${constraint}`}>Missing constraint: {constraint}</li>)}
          </ul>
        </div>
      ) : null}

      {errors.length > 0 ? (
        <p className="runtime-readiness-error" role="status">
          {errors[0].code}: {errors[0].message}
        </p>
      ) : null}

      {recoverySteps.length > 0 ? (
        <div className="runtime-recovery-steps">
          <strong>Run from the repository root</strong>
          <ol>
            {recoverySteps.map((step) => <li key={step}><code>{step}</code></li>)}
          </ol>
        </div>
      ) : (
        <p className="runtime-ready-copy">Database connectivity and the required schema are ready.</p>
      )}
    </section>
  );
}
