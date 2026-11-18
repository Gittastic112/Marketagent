import assert from "node:assert/strict";
import test from "node:test";
import type { EvidencePreviewRow } from "./api/portfolio-evidence.ts";
import { EMPTY_EVIDENCE_FILTER, filterEvidenceRows, nextEvidenceIssue } from "./evidence-import-review.ts";
import { applyPortfolioEvidence, previewPortfolioEvidence } from "./api/portfolio-evidence.ts";

const rows: EvidencePreviewRow[] = [
  { row_index: 2, record_type: "market_price", action: "create", message: "Ready", errors: [] },
  { row_index: 3, record_type: "fx_rate", action: "error", message: "Invalid", errors: [{ row_index: 3, field: "rate", message: "Must be positive" }] },
  { row_index: 4, record_type: "market_price", action: "skip", message: "Exact stored duplicate", errors: [] },
  { row_index: 5, record_type: null, action: "error", message: "Invalid", errors: [{ row_index: 5, field: "record_type", message: "Unsupported" }] },
];

test("preview filtering combines status, type, field and text without changing original rows", () => {
  const snapshot = JSON.stringify(rows);
  assert.deepEqual(filterEvidenceRows(rows, { ...EMPTY_EVIDENCE_FILTER, action: "error" }).map(row => row.row_index), [3, 5]);
  assert.deepEqual(filterEvidenceRows(rows, { ...EMPTY_EVIDENCE_FILTER, recordType: "fx_rate", field: "rate", query: "POSITIVE" }).map(row => row.row_index), [3]);
  assert.deepEqual(filterEvidenceRows(rows, { ...EMPTY_EVIDENCE_FILTER, query: "duplicate" }).map(row => row.row_index), [4]);
  assert.deepEqual(filterEvidenceRows(rows, { ...EMPTY_EVIDENCE_FILTER, recordType: "invalid" }).map(row => row.row_index), [5]);
  assert.equal(JSON.stringify(rows), snapshot);
});

test("issue navigation wraps by source row identity, independent of the visible page", () => {
  assert.equal(nextEvidenceIssue(rows, null, 1), 3);
  assert.equal(nextEvidenceIssue(rows, 3, 1), 5);
  assert.equal(nextEvidenceIssue(rows, 5, 1), 3);
  assert.equal(nextEvidenceIssue(rows, 3, -1), 5);
  assert.equal(nextEvidenceIssue([], 3, 1), null);
});

test("preview and apply send unchanged file bytes and the exact server preview hash through transport", async () => {
  const originalFetch = globalThis.fetch;
  const requests: Array<{ url: string; data: FormData }> = [];
  globalThis.fetch = (async (url, options) => {
    requests.push({ url: String(url), data: options?.body as FormData });
    return Response.json({ data: { content_sha256: "test-hash" }, meta: {}, errors: [] });
  }) as typeof fetch;
  try {
    const file = new File(["record_type,rate\r\nfx_rate,1.250000\r\n"], "evidence.csv", { type: "text/csv" });
    await previewPortfolioEvidence(7, file);
    await applyPortfolioEvidence(7, file, "test-hash");
    assert.ok(requests[0].url.endsWith("/portfolios/7/evidence-bundle/preview"));
    assert.ok(requests[1].url.endsWith("/portfolios/7/evidence-bundle/apply"));
    assert.equal(requests[1].data.get("expected_sha256"), "test-hash");
    assert.equal(await (requests[1].data.get("file") as File).text(), await file.text());
  } finally { globalThis.fetch = originalFetch; }
});
