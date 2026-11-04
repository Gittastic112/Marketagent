import type { BriefPublicCoverage as Coverage, BriefSelectionCounts } from "@/lib/api/daily-brief";

const scopeLabels: Record<Coverage["selection_basis"], string> = {
  since_last_review: "Stored records after the last reviewed brief",
  stored_history: "Stored history at capture",
  dashboard_preview: "Current dashboard preview",
  caller_supplied: "Provided inputs; the full stored inventory was not counted",
};

export function BriefPublicCoverage({ coverage, compact = false }: { coverage?: Coverage | null; compact?: boolean }) {
  if (!coverage) return <section aria-label="Stored source coverage">
    <p className="basis-note"><strong>Coverage not recorded.</strong> This saved output has no stored selection counts. Its original evidence has not been rewritten.</p>
  </section>;
  const rows: Array<[string, BriefSelectionCounts]> = [
    ["Public events", coverage.events],
    ["Failed or partial runs", coverage.failed_runs],
    ["Derived inspection actions", coverage.inspection_actions],
  ];
  return <section aria-label="Stored source coverage">
    <p className="basis-note"><strong>Stored-input selection: {coverage.status}.</strong> {scopeLabels[coverage.selection_basis]}.</p>
    <p className="basis-note">These counts do not establish complete provider coverage or verify source claims.</p>
    <details open={!compact}>
      <summary>Coverage window and counts</summary>
      <p className="basis-note">Captured {coverage.captured_at}. {coverage.window_end_inclusive
        ? `Collection window: ${coverage.window_start_exclusive ? `after ${coverage.window_start_exclusive}` : "all earlier stored history"} through ${coverage.window_end_inclusive}.`
        : "The collection window is unknown."}</p>
      <p className="basis-note">Events use their stored creation time; runs use their start time. The window is separate from publication dates and the brief date.</p>
      <div className="table-wrap" tabIndex={0} aria-label="Stored input selection counts">
        <table>
          <thead><tr><th>Inputs</th><th>Eligible</th><th>Included</th><th>Excluded</th><th>Limit</th></tr></thead>
          <tbody>{rows.map(([label, counts]) => <tr key={label}>
            <th scope="row">{label}</th><td>{counts.eligible_count ?? "Unknown"}</td><td>{counts.included_count}</td>
            <td>{counts.excluded_count ?? "Unknown"}</td><td>{counts.cap ?? "Unknown"}</td>
          </tr>)}</tbody>
        </table>
      </div>
      {rows.map(([label, counts]) => <div key={label}>
        {Object.entries(counts.exclusion_reasons).map(([reason, count]) =>
          <p className="basis-note" key={reason}>{label}: {count} excluded ({reason.replaceAll("_", " ")}).</p>)}
      </div>)}
      {coverage.limitations.map(note => <p className="basis-note" key={note}>{note}</p>)}
    </details>
  </section>;
}
