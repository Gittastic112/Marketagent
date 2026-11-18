import type { EvidencePreviewRow } from "./api/portfolio-evidence.ts";

export type EvidenceReviewFilter = { action: "all" | EvidencePreviewRow["action"]; recordType: string; field: string; query: string };
export const EMPTY_EVIDENCE_FILTER: EvidenceReviewFilter = { action: "all", recordType: "all", field: "all", query: "" };
export const EVIDENCE_REVIEW_PAGE_SIZE = 50;

export function filterEvidenceRows(rows: readonly EvidencePreviewRow[], filter: EvidenceReviewFilter): EvidencePreviewRow[] {
  const query = filter.query.trim().toLocaleLowerCase();
  return rows.filter(row => {
    if (filter.action !== "all" && row.action !== filter.action) return false;
    if (filter.recordType !== "all" && (row.record_type ?? "invalid") !== filter.recordType) return false;
    if (filter.field !== "all" && !row.errors.some(error => error.field === filter.field)) return false;
    return !query || [row.row_index, row.record_type, row.message, ...row.errors.flatMap(error => [error.field, error.message])]
      .join(" ").toLocaleLowerCase().includes(query);
  });
}

/** Navigation retains original CSV row identities, including when the view is filtered. */
export function nextEvidenceIssue(rows: readonly EvidencePreviewRow[], currentRow: number | null, direction: 1 | -1): number | null {
  const issues = rows.filter(row => row.action === "error");
  if (!issues.length) return null;
  const index = issues.findIndex(row => row.row_index === currentRow);
  return issues[index < 0 ? (direction === 1 ? 0 : issues.length - 1) : (index + direction + issues.length) % issues.length].row_index;
}
