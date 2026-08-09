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
      <div style={{ marginBottom: "1rem" }}>
        <strong>{explanation.score_name} - {explanation.label} ({explanation.value})</strong>
        <p className="muted" style={{ margin: "0.25rem 0" }}>Direction: {explanation.direction} | Confidence: {explanation.confidence}</p>
        <p>{explanation.summary}</p>
      </div>
      <div>
        <strong>Inputs Breakdown:</strong>
        {explanation.inputs && explanation.inputs.length > 0 ? (
          <ul className="compact-list" style={{ marginTop: "0.5rem" }}>
            {explanation.inputs.map((input, idx) => (
              <li key={idx}>
                <strong>{input.name}</strong>: {input.value} (Weight: {input.weight}, Contribution: {input.contribution})
                <br />
                <span className="muted">{input.explanation}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">No inputs recorded.</p>
        )}
      </div>
    </div>
  );
}
