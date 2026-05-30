import type { EventRecord, ScoringConfig } from "@/lib/api";

interface ScoreBreakdownProps {
  event: EventRecord;
  config: ScoringConfig;
}

function ScoreBar({ label, score, weight, color }: { label: string; score: number | null; weight: number; color: string }) {
  const value = score ?? 0;
  const weighted = value * weight;
  const pct = Math.min(value * 10, 100); // scores are 0-10

  return (
    <div style={{ marginBottom: "0.75rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8rem", marginBottom: "0.25rem" }}>
        <span style={{ fontWeight: 600 }}>{label}</span>
        <span style={{ color: "var(--text-secondary)" }}>
          {value.toFixed(1)} × {(weight * 100).toFixed(0)}% = <strong>{weighted.toFixed(2)}</strong>
        </span>
      </div>
      <div style={{ height: "6px", borderRadius: "3px", backgroundColor: "var(--bg-secondary)", overflow: "hidden" }}>
        <div
          style={{
            height: "100%",
            width: `${pct}%`,
            backgroundColor: color,
            borderRadius: "3px",
            transition: "width 0.3s ease",
          }}
        />
      </div>
    </div>
  );
}

export function ScoreBreakdown({ event, config }: ScoreBreakdownProps) {
  const credibility = event.credibility_score ?? 0;
  const novelty = event.novelty_score ?? 0;
  const impact = event.impact_score ?? 0;
  const speedValue = event.information_speed === "breaking" ? 10 : event.information_speed === "developing" ? 7 : event.information_speed === "stale" ? 3 : 5;

  const computed =
    credibility * config.weight_credibility +
    novelty * config.weight_novelty +
    impact * config.weight_impact +
    speedValue * config.weight_speed;

  const actual = event.priority_score;

  return (
    <div style={{ padding: "1rem", borderRadius: "8px", border: "1px solid var(--border-color)", backgroundColor: "var(--bg-primary)" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "1rem" }}>
        <h4 style={{ margin: 0, fontSize: "0.9rem", fontWeight: 600 }}>Score Breakdown</h4>
        <div style={{ textAlign: "right" }}>
          <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>Computed: {computed.toFixed(2)}</span>
          {actual != null && (
            <span style={{ marginLeft: "0.75rem", fontSize: "0.8rem", color: actual !== Math.round(computed * 100) / 100 ? "var(--warning)" : "var(--success)" }}>
              Stored: {actual}
            </span>
          )}
        </div>
      </div>

      <ScoreBar label="Credibility" score={event.credibility_score} weight={config.weight_credibility} color="#3b82f6" />
      <ScoreBar label="Novelty" score={event.novelty_score} weight={config.weight_novelty} color="#8b5cf6" />
      <ScoreBar label="Impact" score={event.impact_score} weight={config.weight_impact} color="#f59e0b" />
      <ScoreBar label="Speed" score={speedValue} weight={config.weight_speed} color="#10b981" />

      <div style={{ marginTop: "1rem", paddingTop: "0.75rem", borderTop: "1px solid var(--border-color)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem" }}>
          <span style={{ fontWeight: 600 }}>Formula</span>
          <span style={{ color: "var(--text-secondary)", fontFamily: "monospace", fontSize: "0.75rem" }}>
            ({credibility.toFixed(1)} × {config.weight_credibility}) + ({novelty.toFixed(1)} × {config.weight_novelty}) + ({impact.toFixed(1)} × {config.weight_impact}) + ({speedValue} × {config.weight_speed})
          </span>
        </div>
      </div>
    </div>
  );
}
