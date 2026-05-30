import type { ScoreExplanation } from "@/lib/api";

function factorList(factors: string[] | undefined) {
  if (!factors || factors.length === 0) {
    return <p className="muted">No factors recorded.</p>;
  }
  return (
    <ul className="compact-list">
      {factors.map((factor) => (
        <li key={factor}>{factor}</li>
      ))}
    </ul>
  );
}

export function ScoreExplanationView({ explanation }: { explanation: ScoreExplanation | null }) {
  if (!explanation) {
    return <p className="muted">No score explanation stored.</p>;
  }

  return (
    <div className="score-explanation">
      <div>
        <strong>Credibility {explanation.credibility?.score ?? "-"}</strong>
        {factorList(explanation.credibility?.factors)}
      </div>
      <div>
        <strong>Novelty {explanation.novelty?.score ?? "-"}</strong>
        {factorList(explanation.novelty?.factors)}
      </div>
      <div>
        <strong>Impact {explanation.impact?.score ?? "-"}</strong>
        {factorList(explanation.impact?.factors)}
      </div>
      <div>
        <strong>Speed {explanation.information_speed?.value ?? "-"}</strong>
        {factorList(explanation.information_speed?.factors)}
      </div>
      <div>
        <strong>Priority {explanation.priority?.score ?? "-"}</strong>
        <p className="muted">{explanation.priority?.formula ?? "No formula recorded."}</p>
      </div>
    </div>
  );
}
