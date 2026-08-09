export default function SearchLoading() {
  return (
    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", padding: "4rem" }}>
      <div className="spinner" style={{ width: "2rem", height: "2rem", border: "3px solid var(--border)", borderTopColor: "var(--accent)", borderRadius: "50%", animation: "spin 1s linear infinite" }} />
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
