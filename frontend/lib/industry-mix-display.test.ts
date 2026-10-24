import assert from "node:assert/strict";
import test from "node:test";

import { industryWarningText, industryMixHasEdits } from "./industry-mix-display.ts";

test("benchmark warnings show readable fields while retaining the reason", () => {
  assert.equal(
    industryWarningText("revenueGrowthPriors.industryHistorical5Y is unavailable: matched periods are required."),
    "Historical five-year growth is unavailable: matched periods are required.",
  );
  assert.equal(
    industryWarningText("reinvestmentPriors.suggestedSalesToCapital is unavailable because data is missing for: Services"),
    "Suggested sales-to-capital ratio is unavailable because data is missing for: Services",
  );
  assert.equal(industryWarningText("Financing totals are unavailable."), "Financing totals are unavailable.");
});

test("unknown benchmark fields stay visible without internal key syntax", () => {
  assert.equal(industryWarningText("returnPriors.newReturnField is unavailable."), "New return field is unavailable.");
});

const saved = {
  as_of_date: "2025-09-27", source_document_id: null, notes: "Reviewed basis",
  allocations: [{ segment_name: "Products", industry_name: "Computers/Peripherals", weight_percent: 73.770248 },
    { segment_name: "Services", industry_name: "Software (Internet)", weight_percent: 26.229752 }],
};
const editor = {
  asOfDate: "2025-09-27", sourceDocumentId: null, notes: "Reviewed basis",
  rows: saved.allocations.map(row => ({ segmentName: row.segment_name, industryName: row.industry_name, weightPercent: row.weight_percent })),
};

test("display rounding never changes the saved allocation basis", () => {
  assert.equal(industryMixHasEdits(saved, editor), false);
  assert.equal(industryMixHasEdits(saved, { ...editor, rows: editor.rows.map(row => ({ ...row, weightPercent: Number(row.weightPercent.toFixed(2)) })) }), true);
});

test("drafting requires saving row, date, source or note changes", () => {
  for (const change of [
    { ...editor, asOfDate: "2026-09-27" }, { ...editor, sourceDocumentId: 4 },
    { ...editor, notes: "Different basis" }, { ...editor, rows: editor.rows.slice(0, 1) },
    { ...editor, rows: editor.rows.map(row => ({ ...row, industryName: "Diversified" })) },
  ]) assert.equal(industryMixHasEdits(saved, change), true);
  assert.equal(industryMixHasEdits(null, editor), true);
  assert.equal(industryMixHasEdits(saved, { ...editor, notes: " Reviewed basis " }), false);
});
