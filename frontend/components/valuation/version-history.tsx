"use client";

import Link from "next/link";
import { useState } from "react";
import { exportSavedValuation } from "@/lib/api/valuation";
import type { DcfAssumptionSet } from "@/lib/api/valuation";
import type { ValuationVersionReceipt } from "@/lib/api/valuation-preview";

export function ValuationVersionHistory({ companyId, modelId, versions, selectedId, receipts }: {
  companyId: number; modelId: number; versions: DcfAssumptionSet[]; selectedId?: number;
  receipts: ValuationVersionReceipt[] | null;
}) {
  const selected = versions.find(v => v.id === selectedId);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  async function download() {
    if (!selected || busy) return;
    setBusy(true); setError(null);
    try {
    const artifact = await exportSavedValuation(modelId, selected.id);
    const url = URL.createObjectURL(new Blob([JSON.stringify(artifact, null, 2)], { type: "application/json" }));
    const link = document.createElement("a"); link.href = url; link.download = `valuation-${modelId}-version-${selected.id}.json`;
    link.click(); URL.revokeObjectURL(url);
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Saved version export unavailable. Retry."); }
    finally { setBusy(false); }
  }
  return <section className="panel panel-content valuation-version-panel" aria-label="Saved valuation versions">
    <details><summary>Saved versions and reasons ({versions.length})</summary>
      {receipts === null && <p role="alert">Version reasons could not be loaded. Saved calculations remain available.</p>}
      <div className="table-wrap" role="region" aria-label="Valuation version history" tabIndex={0}>
        <table><thead><tr><th>Version</th><th>Saved</th><th>Research date</th><th>Reason</th></tr></thead><tbody>
          {versions.map((version, i) => { const receipt = receipts?.find(r => r.assumption_set_id === version.id);
            return <tr key={version.id}><th scope="row"><Link href={`/companies/${companyId}/valuation/${modelId}${i ? `?version=${version.id}` : ""}`}>
              #{version.id}{i === 0 ? " · latest" : ""}{version.id === selectedId ? " · selected" : ""}</Link></th>
              <td>{new Date(version.created_at).toLocaleString()}</td><td>{receipt?.valuation_date ?? "Not recorded"}</td>
              <td>{receipt?.reason ?? "No version reason recorded"}</td></tr>; })}
        </tbody></table>
      </div>
    </details>
    <button className="secondary-button" type="button" onClick={download} disabled={!selected || busy}>{busy ? "Preparing saved archive…" : `Export exact saved version #${selectedId}`}</button>
    {error && <p role="alert">{error}</p>}
    <p>The export preserves the original stored calculations and warnings. Current interpretations on this page may differ. Unsaved edits are excluded.</p>
  </section>;
}
