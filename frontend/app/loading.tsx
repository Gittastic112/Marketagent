export default function Loading() {
  return (
    <div className="route-state" role="status" aria-live="polite">
      <div className="route-state-heading skeleton-line" />
      <div className="skeleton-grid">
        <div className="skeleton-panel" />
        <div className="skeleton-panel" />
        <div className="skeleton-panel" />
      </div>
      <span className="sr-only">Loading workspace</span>
    </div>
  );
}
