export function TopBar() {
  return (
    <header className="topbar">
      <div className="topbar-search">
        <input type="search" placeholder="Search companies, narratives, or documents... (Press '/' to focus)" aria-label="Global search" />
      </div>
      <div className="topbar-actions">
        <div className="data-freshness">
          <span className="status-indicator"></span>
          Data up to date
        </div>
        <div className="user-controls">
          <button className="secondary-button" aria-label="Settings">⚙️</button>
        </div>
      </div>
    </header>
  );
}
