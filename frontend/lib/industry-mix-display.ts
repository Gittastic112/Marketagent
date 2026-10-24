/** Presentation and edit-state checks only. Financial aggregation stays in the backend. */
const benchmarkLabels: Record<string, string> = {
  industryHistorical5Y: "Historical five-year growth",
  industryExpected2Y: "Expected two-year growth",
  industryExpected5Y: "Expected five-year growth",
  suggestedYears1To2: "Suggested growth for years 1–2",
  suggestedYears3To5: "Suggested growth for years 3–5",
  industryUnadjustedOperatingMargin: "Reported operating margin",
  industryLeaseAdjustedMargin: "Lease-adjusted operating margin",
  industryLeaseRdAdjustedMargin: "Lease and research-adjusted operating margin",
  suggestedTargetMargin: "Suggested target margin",
  industrySalesToCapital: "Industry sales-to-capital ratio",
  suggestedSalesToCapital: "Suggested sales-to-capital ratio",
  industryNetCapexToSales: "Net capital spending as a share of revenue",
  industryWorkingCapitalToSales: "Working capital as a share of revenue",
  industryRoc: "Return on capital",
  industryRoe: "Return on equity",
  industryRoeAdjustedForRd: "Research-adjusted return on equity",
  suggestedTerminalRoc: "Suggested long-term return on capital",
  industryDebtSignals: "Industry debt indicators",
  suggestedTargetDebtRatio: "Suggested debt share of capital",
};

function readableField(value: string): string {
  const text = value.replace(/([a-z0-9])([A-Z])/g, "$1 $2").replaceAll("_", " ").toLowerCase();
  return text.charAt(0).toUpperCase() + text.slice(1);
}

export function industryWarningText(warning: string): string {
  return warning.replace(/\b(?:revenueGrowthPriors|marginPriors|reinvestmentPriors|returnPriors|capitalStructurePriors)\.([A-Za-z0-9_]+)/g,
    (_match, field: string) => benchmarkLabels[field] ?? readableField(field));
}

type SavedMix = {
  as_of_date: string | null; source_document_id: number | null; notes: string | null;
  allocations: Array<{ segment_name: string; industry_name: string; weight_percent: number }>;
};
type MixEditor = {
  asOfDate: string; sourceDocumentId: number | null; notes: string;
  rows: Array<{ segmentName: string; industryName: string; weightPercent: number }>;
};

export function industryMixHasEdits(saved: SavedMix | null, editor: MixEditor): boolean {
  if (!saved) return true;
  return (saved.as_of_date ?? "") !== editor.asOfDate
    || saved.source_document_id !== editor.sourceDocumentId
    || (saved.notes ?? "").trim() !== editor.notes.trim()
    || saved.allocations.length !== editor.rows.length
    || saved.allocations.some((allocation, index) => {
      const row = editor.rows[index];
      return allocation.segment_name !== row.segmentName.trim()
        || allocation.industry_name !== row.industryName
        || allocation.weight_percent !== row.weightPercent;
    });
}
