import React, { useState } from 'react';

export function AiOutputMetadata({ aiOutput }: { aiOutput: any }) {
  const [showDetails, setShowDetails] = useState(false);

  if (!aiOutput) return null;

  return (
    <div style={{ marginTop: '0.75rem', padding: '0.75rem', backgroundColor: 'var(--bg-primary)', border: '1px solid var(--border-color)', borderRadius: '0.5rem', fontSize: '0.8rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <span style={{ fontWeight: 600, color: 'var(--muted)' }}>Model:</span>
          <span>{aiOutput.model_name}</span>
          {aiOutput.is_mock && <span style={{ backgroundColor: 'var(--warning-color)', color: 'white', padding: '0.1rem 0.4rem', borderRadius: '0.25rem', fontSize: '0.7rem', fontWeight: 'bold' }}>MOCK</span>}
          {aiOutput.is_blocked && <span style={{ backgroundColor: 'var(--error-color)', color: 'white', padding: '0.1rem 0.4rem', borderRadius: '0.25rem', fontSize: '0.7rem', fontWeight: 'bold' }}>UNSUPPORTED CLAIM</span>}
        </div>
        <button
          onClick={() => setShowDetails(!showDetails)}
          style={{ background: 'none', border: 'none', color: 'var(--accent-color)', cursor: 'pointer', fontSize: '0.8rem', padding: 0 }}
        >
          {showDetails ? 'Hide Provenance' : 'View Provenance'}
        </button>
      </div>

      {aiOutput.is_blocked && (
        <div style={{ marginTop: '0.5rem', color: 'var(--error-color)', fontWeight: 500 }}>
          Disclaimer: This response contains factual claims that could not be verified against the provided source evidence. Please independently verify the claims.
        </div>
      )}

      {showDetails && (
        <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px dashed var(--border-color)' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <span style={{ color: 'var(--muted)' }}>Execution:</span>
            <span>{aiOutput.execution_status} {aiOutput.failure_code ? `(${aiOutput.failure_code})` : ''}</span>
            <span style={{ color: 'var(--muted)' }}>Confidence:</span>
            <span>{aiOutput.confidence_label}</span>
            <span style={{ color: 'var(--muted)' }}>Human review:</span>
            <span>{aiOutput.human_review_status}</span>
            <span style={{ color: 'var(--muted)' }}>Prompt Version:</span>
            <span style={{ fontFamily: 'monospace' }}>{aiOutput.prompt_version}</span>
          </div>

          {aiOutput.citations_json && Array.isArray(aiOutput.citations_json) && aiOutput.citations_json.length > 0 && (
            <div style={{ marginTop: '0.5rem' }}>
              <span style={{ color: 'var(--muted)', display: 'block', marginBottom: '0.25rem' }}>Citations:</span>
              <ul style={{ margin: 0, paddingLeft: '1.25rem' }}>
                {aiOutput.citations_json.map((cit: any, i: number) => (
                  <li key={i}>
                    <strong>[{cit.source_id}]</strong>
                    {cit.quote && <span style={{ fontStyle: 'italic', marginLeft: '0.5rem' }}>"{cit.quote}"</span>}
                    <span style={{ marginLeft: '0.5rem' }}>{cit.status}</span>
                    {cit.reason && <span style={{ marginLeft: '0.5rem' }}>({cit.reason})</span>}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
